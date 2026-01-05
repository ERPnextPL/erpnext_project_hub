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

export const useMyTasksStore = defineStore("myTasks", () => {
	// State
	const tasks = ref([]);
	const loading = ref(false);
	const error = ref(null);
	const total = ref(0);
	const selectedTask = ref(null);
	const drawerOpen = ref(false);
	const drawerMode = ref("view");
	const drawerPreset = ref(null);
	const drawerAction = ref(null);
	const inlineDropdown = ref(null); // { taskName: string, type: 'status' | 'priority' }
	const viewOptions = ref({
		groupByStatus: false,
		showHierarchy: false,
	});
	const expandedParents = ref(new Set());

	// Filter state
	const filters = ref({
		status: [],
		priority: [],
		project: null,
		dueFilter: null, // 'today', 'week', 'overdue', 'all'
		search: "",
		sortBy: "default",
	});

	// Metadata
	const projects = ref([]);
	const statuses = ref([]);
	const priorities = ref([]);

	// Optimistic update tracking
	const pendingUpdates = ref(new Map());

	// Computed
	const hasActiveFilters = computed(() => {
		return (
			filters.value.status.length > 0 ||
			filters.value.priority.length > 0 ||
			filters.value.project ||
			filters.value.dueFilter ||
			filters.value.search
		);
	});

	// Actions
	async function fetchTasks() {
		loading.value = true;
		error.value = null;

		try {
			const params = {};

			if (filters.value.status.length > 0) {
				params.status = filters.value.status.join(",");
			}
			if (filters.value.priority.length > 0) {
				params.priority = filters.value.priority.join(",");
			}
			if (filters.value.project) {
				params.project = filters.value.project;
			}
			if (filters.value.dueFilter && filters.value.dueFilter !== "all") {
				params.due_filter = filters.value.dueFilter;
			}
			if (filters.value.search) {
				params.search = filters.value.search;
			}
			if (filters.value.sortBy) {
				params.sort_by = filters.value.sortBy;
			}

			const data = await apiCall("erpnext_projekt_hub.api.project_hub.get_my_tasks", params);

			if (data) {
				tasks.value = data.tasks || [];
				total.value = data.total || 0;
			}
		} catch (err) {
			error.value = err.message || "Failed to fetch tasks";
			console.error("Failed to fetch my tasks:", err);
		} finally {
			loading.value = false;
		}
	}

	async function fetchProjects() {
		try {
			const data = await apiCall(
				"erpnext_projekt_hub.api.project_hub.get_my_tasks_projects",
				{}
			);
			projects.value = data || [];
		} catch (err) {
			console.error("Failed to fetch projects:", err);
		}
	}

	async function fetchMetadata() {
		try {
			const [statusData, priorityData] = await Promise.all([
				apiCall("erpnext_projekt_hub.api.project_hub.get_task_statuses", {}),
				apiCall("erpnext_projekt_hub.api.project_hub.get_task_priorities", {}),
			]);
			statuses.value = statusData || [];
			priorities.value = priorityData || [];
		} catch (err) {
			console.error("Failed to fetch metadata:", err);
			// Fallback values
			statuses.value = [
				"Open",
				"Working",
				"Pending Review",
				"Completed",
				"Overdue",
				"Cancelled",
			];
			priorities.value = ["Low", "Medium", "High", "Urgent"];
		}
	}

	async function quickUpdateTask(taskName, updates) {
		// Optimistic update
		const taskIndex = tasks.value.findIndex((t) => t.name === taskName);
		if (taskIndex === -1) return;

		const originalTask = { ...tasks.value[taskIndex] };

		// Apply optimistic update
		tasks.value[taskIndex] = { ...tasks.value[taskIndex], ...updates };
		pendingUpdates.value.set(taskName, originalTask);

		try {
			const data = await apiCall("erpnext_projekt_hub.api.project_hub.quick_update_task", {
				task_name: taskName,
				...updates,
			});

			if (data) {
				// Update with server response
				tasks.value[taskIndex] = data;

				// Update selected task if it's the same
				if (selectedTask.value?.name === taskName) {
					selectedTask.value = data;
				}
			}

			pendingUpdates.value.delete(taskName);
			return data;
		} catch (err) {
			// Rollback on error
			if (pendingUpdates.value.has(taskName)) {
				tasks.value[taskIndex] = pendingUpdates.value.get(taskName);
				pendingUpdates.value.delete(taskName);
			}
			console.error("Failed to update task:", err);
			throw err;
		}
	}

	async function createTask(taskData) {
		try {
			const data = await apiCall(
				"erpnext_projekt_hub.api.project_hub.create_my_task",
				taskData
			);

			if (data) {
				// Add to beginning of list
				tasks.value.unshift(data);
				total.value++;

				if (window.frappe) {
					frappe.show_alert({
						message: "Task created successfully",
						indicator: "green",
					});
				}

				return data;
			}
		} catch (err) {
			console.error("Failed to create task:", err);
			throw err;
		}
	}

	async function updateTaskFull(taskName, updates, options = {}) {
		try {
			const data = await apiCall("erpnext_projekt_hub.api.project_hub.update_task", {
				task_name: taskName,
				...updates,
			});

			if (data) {
				const taskIndex = tasks.value.findIndex((t) => t.name === taskName);
				if (taskIndex !== -1) {
					// Merge with existing data (keep project_name etc)
					tasks.value[taskIndex] = { ...tasks.value[taskIndex], ...data };
				}

				if (selectedTask.value?.name === taskName) {
					selectedTask.value = { ...selectedTask.value, ...data };
				}

				if (options.showAlert !== false && window.frappe) {
					frappe.show_alert({
						message: "Task updated successfully",
						indicator: "green",
					});
				}

				return data;
			}
		} catch (err) {
			console.error("Failed to update task:", err);
			throw err;
		}
	}

	async function getTaskDetail(taskName) {
		try {
			const data = await apiCall("erpnext_projekt_hub.api.project_hub.get_task_detail", {
				task_name: taskName,
			});
			return data;
		} catch (err) {
			console.error("Failed to get task detail:", err);
			throw err;
		}
	}

	function selectTask(task) {
		selectedTask.value = task;
		drawerMode.value = "view";
		drawerPreset.value = null;
		drawerAction.value = null;
		drawerOpen.value = true;
	}

	function openNewTask(preset = null) {
		selectedTask.value = null;
		drawerMode.value = "new";
		drawerPreset.value = preset;
		drawerAction.value = null;
		drawerOpen.value = true;
	}

	function openNewSubtask(parentTask) {
		if (!parentTask) return;
		if (parentTask.status === "Completed" || parentTask.status === "Cancelled") return;
		openNewTask({
			parent_task: parentTask.name,
			project: parentTask.project,
			exp_end_date: parentTask.exp_end_date || "",
			status: parentTask.status,
			priority: parentTask.priority,
		});
	}

	function openTimelog(task) {
		if (!task) return;
		selectedTask.value = task;
		drawerMode.value = "view";
		drawerPreset.value = null;
		drawerAction.value = { type: "timelog", taskName: task.name };
		drawerOpen.value = true;
	}

	function clearDrawerAction() {
		drawerAction.value = null;
	}

	function setViewOption(key, value) {
		viewOptions.value = { ...viewOptions.value, [key]: value };
		if (key === "showHierarchy" && value) {
			// B1: default collapsed
			expandedParents.value = new Set();
		}
		if (key === "showHierarchy" && !value) {
			expandedParents.value = new Set();
		}
	}

	function toggleViewOption(key) {
		setViewOption(key, !viewOptions.value?.[key]);
	}

	function toggleExpandParent(taskName) {
		const next = new Set(expandedParents.value);
		if (next.has(taskName)) {
			next.delete(taskName);
		} else {
			next.add(taskName);
		}
		expandedParents.value = next;
	}

	function closeDrawer() {
		drawerOpen.value = false;
		// Delay clearing selected task for animation
		setTimeout(() => {
			selectedTask.value = null;
			drawerMode.value = "view";
			drawerPreset.value = null;
			drawerAction.value = null;
		}, 300);
	}

	function openInlineDropdown(taskName, type) {
		inlineDropdown.value = { taskName, type };
	}

	function toggleInlineDropdown(taskName, type) {
		if (inlineDropdown.value?.taskName === taskName && inlineDropdown.value?.type === type) {
			inlineDropdown.value = null;
			return;
		}
		inlineDropdown.value = { taskName, type };
	}

	function closeInlineDropdown() {
		inlineDropdown.value = null;
	}

	function setFilter(key, value) {
		filters.value[key] = value;
	}

	function clearFilters() {
		filters.value = {
			status: [],
			priority: [],
			project: null,
			dueFilter: null,
			search: "",
			sortBy: "default",
		};
	}

	function toggleStatusFilter(status) {
		const index = filters.value.status.indexOf(status);
		if (index > -1) {
			filters.value.status.splice(index, 1);
		} else {
			filters.value.status.push(status);
		}
		fetchTasks();
	}

	function togglePriorityFilter(priority) {
		const index = filters.value.priority.indexOf(priority);
		if (index > -1) {
			filters.value.priority.splice(index, 1);
		} else {
			filters.value.priority.push(priority);
		}
		fetchTasks();
	}

	// ==========================================================================
	// TIMELOG FUNCTIONS
	// ==========================================================================

	const taskTimelogs = ref({});
	const activityTypes = ref([]);

	async function fetchActivityTypes() {
		try {
			const data = await apiCall(
				"erpnext_projekt_hub.api.project_hub.get_activity_types",
				{}
			);
			activityTypes.value = data || [];
			return data;
		} catch (error) {
			console.error("Failed to fetch activity types:", error);
			activityTypes.value = [];
		}
	}

	async function fetchTaskTimelogs(taskName) {
		try {
			const data = await apiCall("erpnext_projekt_hub.api.project_hub.get_task_timelogs", {
				task_name: taskName,
			});
			taskTimelogs.value[taskName] = data;
			return data;
		} catch (error) {
			console.error("Failed to fetch task timelogs:", error);
			throw error;
		}
	}

	async function createTimelog(timelogData) {
		try {
			const data = await apiCall(
				"erpnext_projekt_hub.api.project_hub.create_timelog",
				timelogData
			);
			// Refresh timelogs for this task
			if (timelogData.task) {
				await fetchTaskTimelogs(timelogData.task);
			}
			return data;
		} catch (error) {
			console.error("Failed to create timelog:", error);
			throw error;
		}
	}

	async function deleteTimelog(timelogName, taskName) {
		try {
			await apiCall("erpnext_projekt_hub.api.project_hub.delete_timelog", {
				timelog_name: timelogName,
			});
			// Refresh timelogs for this task
			if (taskName) {
				await fetchTaskTimelogs(taskName);
			}
			return true;
		} catch (error) {
			console.error("Failed to delete timelog:", error);
			throw error;
		}
	}

	return {
		// State
		tasks,
		loading,
		error,
		total,
		selectedTask,
		drawerOpen,
		drawerMode,
		drawerPreset,
		drawerAction,
		inlineDropdown,
		viewOptions,
		expandedParents,
		filters,
		projects,
		statuses,
		priorities,
		taskTimelogs,
		activityTypes,
		// Computed
		hasActiveFilters,
		// Actions
		fetchTasks,
		fetchProjects,
		fetchMetadata,
		quickUpdateTask,
		createTask,
		updateTaskFull,
		getTaskDetail,
		selectTask,
		openNewTask,
		openNewSubtask,
		openTimelog,
		clearDrawerAction,
		setViewOption,
		toggleViewOption,
		toggleExpandParent,
		closeDrawer,
		openInlineDropdown,
		toggleInlineDropdown,
		closeInlineDropdown,
		setFilter,
		clearFilters,
		toggleStatusFilter,
		togglePriorityFilter,
		// Timelog actions
		fetchActivityTypes,
		fetchTaskTimelogs,
		createTimelog,
		deleteTimelog,
	};
});
