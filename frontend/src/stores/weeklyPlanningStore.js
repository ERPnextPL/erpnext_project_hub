import { defineStore } from "pinia";
import { ref, computed } from "vue";

// Helper to get CSRF token
function getCsrfToken() {
	if (window.frappe && window.frappe.csrf_token && window.frappe.csrf_token !== "None") {
		return window.frappe.csrf_token;
	}
	if (window.csrf_token && window.csrf_token !== "{{ csrf_token }}") {
		return window.csrf_token;
	}
	return "";
}

// Helper for API calls with FormData
async function apiCall(method, params = {}) {
	const csrfToken = getCsrfToken();

	const formData = new FormData();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined) {
			formData.append(key, value);
		}
	});

	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: {
			"X-Frappe-CSRF-Token": csrfToken,
		},
		body: formData,
	});

	const data = await response.json();

	// Display server messages if present
	if (data._server_messages && window.frappe) {
		try {
			const messages = JSON.parse(data._server_messages);
			if (Array.isArray(messages)) {
				messages.forEach((msg) => {
					try {
						const msgData = JSON.parse(msg);
						if (msgData.message) {
							frappe.show_alert({
								message: msgData.message,
								indicator: msgData.indicator || "blue",
							});
						}
					} catch (e) {
						if (typeof msg === "string") {
							frappe.show_alert({ message: msg, indicator: "blue" });
						}
					}
				});
			}
		} catch (e) {
			console.error("Error parsing server messages:", e);
		}
	}

	if (!response.ok) {
		const errorMsg = data.exception || data._server_messages || "API Error";
		if (window.frappe) {
			frappe.show_alert({ message: errorMsg, indicator: "red" });
		}
		throw new Error(errorMsg);
	}
	return data.message;
}

// Helper to get Monday of current week
function getMondayOfWeek(date = new Date()) {
	const d = new Date(date);
	const day = d.getDay();
	const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
	return new Date(d.setDate(diff));
}

// Helper to format date as YYYY-MM-DD
function formatDate(date) {
	const d = new Date(date);
	return d.toISOString().split("T")[0];
}

export const useWeeklyPlanningStore = defineStore("weeklyPlanning", () => {
	// State
	const currentWeekStart = ref(null); // Monday of current week
	const assignments = ref([]); // Daily assignments
	const employees = ref([]); // Available employees
	const taskPool = ref([]); // Unassigned tasks
	const capacities = ref({}); // {employee: {date: hours}}
	const loading = ref(false);
	const selectedEmployee = ref(null); // Filter
	const selectedProjects = ref([]); // Filter
	const showResourcePool = ref(false);
	const draggedTask = ref(null);
	const resourcePoolData = ref([]); // Resource pool summary

	// Initialize to current week
	if (!currentWeekStart.value) {
		currentWeekStart.value = getMondayOfWeek();
	}

	// Computed
	const weekDates = computed(() => {
		if (!currentWeekStart.value) return [];

		const dates = [];
		for (let i = 0; i < 5; i++) {
			// Mon-Fri
			const date = new Date(currentWeekStart.value);
			date.setDate(date.getDate() + i);
			dates.push(formatDate(date));
		}
		return dates;
	});

	const employeeCapacitySummary = computed(() => {
		const summary = {};

		employees.value.forEach((emp) => {
			const empCapacities = capacities.value[emp.name] || {};
			let totalAllocated = 0;

			weekDates.value.forEach((date) => {
				totalAllocated += empCapacities[date] || 0;
			});

			const totalCapacity = 5 * 8; // 5 days × 8 hours
			const available = totalCapacity - totalAllocated;

			summary[emp.name] = {
				employee: emp.name,
				employee_name: emp.employee_name,
				designation: emp.designation,
				department: emp.department,
				total_capacity: totalCapacity,
				allocated: totalAllocated,
				available: available,
				availability_percent: (available / totalCapacity) * 100,
			};
		});

		return summary;
	});

	const filteredEmployees = computed(() => {
		if (selectedEmployee.value) {
			return employees.value.filter((emp) => emp.name === selectedEmployee.value);
		}
		return employees.value;
	});

	// Actions
	async function fetchWeeklyPlan(startDate = null) {
		loading.value = true;

		try {
			if (startDate) {
				currentWeekStart.value = new Date(startDate);
			}

			const params = {
				start_date: formatDate(currentWeekStart.value),
			};

			if (selectedEmployee.value) {
				params.employees = selectedEmployee.value;
			}

			if (selectedProjects.value && selectedProjects.value.length > 0) {
				params.projects = selectedProjects.value.join(",");
			}

			const data = await apiCall(
				"projekt_hub_pro.project_hub_pro.api.weekly_planner.get_weekly_plan_data",
				params
			);

			if (data) {
				assignments.value = data.assignments || [];
				employees.value = data.employees || [];
				capacities.value = data.daily_capacities || {};
				taskPool.value = data.task_pool || [];
			}
		} catch (err) {
			console.error("Failed to fetch weekly plan:", err);
			if (window.frappe) {
				frappe.show_alert({
					message: "Failed to load weekly plan",
					indicator: "red",
				});
			}
		} finally {
			loading.value = false;
		}
	}

	async function fetchTaskPool() {
		try {
			const params = {};

			if (selectedProjects.value && selectedProjects.value.length > 0) {
				params.projects = selectedProjects.value.join(",");
			}

			const data = await apiCall(
				"projekt_hub_pro.project_hub_pro.api.weekly_planner.get_task_pool",
				params
			);

			taskPool.value = data || [];
		} catch (err) {
			console.error("Failed to fetch task pool:", err);
		}
	}

	async function createAssignment(employee, date, task, hours) {
		try {
			const data = await apiCall(
				"projekt_hub_pro.project_hub_pro.api.weekly_planner.create_daily_assignment",
				{
					employee: employee,
					assignment_date: date,
					task: task,
					allocated_hours: hours,
				}
			);

			if (data) {
				// Add to assignments
				assignments.value.push(data);

				// Update capacities
				if (!capacities.value[employee]) {
					capacities.value[employee] = {};
				}
				if (!capacities.value[employee][date]) {
					capacities.value[employee][date] = 0;
				}
				capacities.value[employee][date] += parseFloat(hours);

				if (window.frappe) {
					frappe.show_alert({
						message: "Task assigned successfully",
						indicator: "green",
					});
				}

				return data;
			}
		} catch (err) {
			console.error("Failed to create assignment:", err);
			throw err;
		}
	}

	async function updateAssignment(id, hours = null, status = null) {
		try {
			const params = { assignment_id: id };
			if (hours !== null) params.allocated_hours = hours;
			if (status !== null) params.status = status;

			const data = await apiCall(
				"projekt_hub_pro.project_hub_pro.api.weekly_planner.update_daily_assignment",
				params
			);

			if (data) {
				// Update in local state
				const index = assignments.value.findIndex((a) => a.name === id);
				if (index !== -1) {
					const oldAssignment = assignments.value[index];
					const oldHours = oldAssignment.allocated_hours;

					assignments.value[index] = data;

					// Update capacities
					if (hours !== null) {
						const emp = data.employee;
						const date = data.assignment_date;
						const hoursDiff = parseFloat(hours) - parseFloat(oldHours);

						if (capacities.value[emp] && capacities.value[emp][date] !== undefined) {
							capacities.value[emp][date] += hoursDiff;
						}
					}
				}

				if (window.frappe) {
					frappe.show_alert({
						message: "Assignment updated successfully",
						indicator: "green",
					});
				}

				return data;
			}
		} catch (err) {
			console.error("Failed to update assignment:", err);
			throw err;
		}
	}

	async function deleteAssignment(id) {
		try {
			// Find assignment to get employee and date for capacity update
			const assignment = assignments.value.find((a) => a.name === id);

			await apiCall(
				"projekt_hub_pro.project_hub_pro.api.weekly_planner.delete_daily_assignment",
				{ assignment_id: id }
			);

			// Remove from local state
			const index = assignments.value.findIndex((a) => a.name === id);
			if (index !== -1) {
				assignments.value.splice(index, 1);
			}

			// Update capacities
			if (assignment) {
				const emp = assignment.employee;
				const date = assignment.assignment_date;
				if (capacities.value[emp] && capacities.value[emp][date] !== undefined) {
					capacities.value[emp][date] -= parseFloat(assignment.allocated_hours || 0);
				}
			}

			if (window.frappe) {
				frappe.show_alert({
					message: "Assignment deleted successfully",
					indicator: "green",
				});
			}
		} catch (err) {
			console.error("Failed to delete assignment:", err);
			throw err;
		}
	}

	async function fetchResourcePoolSummary() {
		try {
			const data = await apiCall(
				"projekt_hub_pro.project_hub_pro.api.weekly_planner.get_resource_pool_summary",
				{ start_date: formatDate(currentWeekStart.value) }
			);

			resourcePoolData.value = data || [];
		} catch (err) {
			console.error("Failed to fetch resource pool summary:", err);
		}
	}

	async function generateTimesheets() {
		try {
			const data = await apiCall(
				"projekt_hub_pro.project_hub_pro.api.weekly_planner.generate_timesheets_from_plan",
				{ start_date: formatDate(currentWeekStart.value) }
			);

			if (data && data.length > 0) {
				// Refresh weekly plan to show updated statuses
				await fetchWeeklyPlan();

				if (window.frappe) {
					frappe.show_alert({
						message: `Created ${data.length} timesheet(s) successfully`,
						indicator: "green",
					});
				}

				return data;
			}
		} catch (err) {
			console.error("Failed to generate timesheets:", err);
			throw err;
		}
	}

	function navigateWeek(direction) {
		const current = new Date(currentWeekStart.value);
		if (direction === "prev") {
			current.setDate(current.getDate() - 7);
		} else if (direction === "next") {
			current.setDate(current.getDate() + 7);
		} else if (direction === "today") {
			currentWeekStart.value = getMondayOfWeek();
			fetchWeeklyPlan();
			return;
		}

		currentWeekStart.value = current;
		fetchWeeklyPlan();
	}

	function goToCurrentWeek() {
		navigateWeek("today");
	}

	function setFilter(key, value) {
		if (key === "employee") {
			selectedEmployee.value = value;
		} else if (key === "projects") {
			selectedProjects.value = value;
		}
		fetchWeeklyPlan();
	}

	function clearFilters() {
		selectedEmployee.value = null;
		selectedProjects.value = [];
		fetchWeeklyPlan();
	}

	function toggleResourcePool() {
		showResourcePool.value = !showResourcePool.value;
		if (showResourcePool.value) {
			fetchResourcePoolSummary();
		}
	}

	// Get assignments for specific employee and date
	function getAssignmentsForEmployeeAndDate(employee, date) {
		return assignments.value.filter(
			(a) => a.employee === employee && a.assignment_date === date
		);
	}

	// Get total hours for employee on date
	function getHoursForEmployeeAndDate(employee, date) {
		if (capacities.value[employee] && capacities.value[employee][date]) {
			return capacities.value[employee][date];
		}
		return 0;
	}

	return {
		// State
		currentWeekStart,
		assignments,
		employees,
		taskPool,
		capacities,
		loading,
		selectedEmployee,
		selectedProjects,
		showResourcePool,
		draggedTask,
		resourcePoolData,
		// Computed
		weekDates,
		employeeCapacitySummary,
		filteredEmployees,
		// Actions
		fetchWeeklyPlan,
		fetchTaskPool,
		createAssignment,
		updateAssignment,
		deleteAssignment,
		fetchResourcePoolSummary,
		generateTimesheets,
		navigateWeek,
		goToCurrentWeek,
		setFilter,
		clearFilters,
		toggleResourcePool,
		getAssignmentsForEmployeeAndDate,
		getHoursForEmployeeAndDate,
	};
});
