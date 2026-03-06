import { defineStore } from "pinia";
import { ref, computed } from "vue";

// ---------------------------------------------------------------------------
// API helper
// ---------------------------------------------------------------------------

function getCsrfToken() {
	if (window.frappe?.csrf_token && window.frappe.csrf_token !== "None") {
		return window.frappe.csrf_token;
	}
	if (window.csrf_token && window.csrf_token !== "{{ csrf_token }}") {
		return window.csrf_token;
	}
	return "";
}

async function apiCall(method, params = {}) {
	const formData = new FormData();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined && value !== "") {
			formData.append(key, typeof value === "object" ? JSON.stringify(value) : String(value));
		}
	});

	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: { "X-Frappe-CSRF-Token": getCsrfToken() },
		body: formData,
	});

	const data = await response.json();

	if (!response.ok) {
		let errorMsg = "API Error";
		try {
			if (data.exception) errorMsg = data.exception;
			else if (data._server_messages) {
				const msgs = JSON.parse(data._server_messages);
				errorMsg = JSON.parse(msgs[0]).message || msgs[0];
			}
		} catch (error) {
			console.warn("[CapacityPlanning] Failed to parse server error payload", error);
		}
		throw new Error(errorMsg);
	}
	return data.message;
}

// ---------------------------------------------------------------------------
// Week utilities
// ---------------------------------------------------------------------------

export function getMondayOf(date = new Date()) {
	const d = new Date(date);
	const day = d.getDay();
	const diff = day === 0 ? -6 : 1 - day;
	d.setDate(d.getDate() + diff);
	return d.toISOString().split("T")[0];
}

export function shiftWeek(mondayIso, weeks) {
	const d = new Date(mondayIso);
	d.setDate(d.getDate() + weeks * 7);
	return d.toISOString().split("T")[0];
}

export function formatDayHeader(isoDate, locale = "pl-PL") {
	return new Intl.DateTimeFormat(locale, {
		weekday: "short",
		day: "numeric",
		month: "short",
	}).format(new Date(isoDate + "T12:00:00"));
}

export function formatWeekLabel(mondayIso, locale = "pl-PL") {
	const mon = new Date(mondayIso + "T12:00:00");
	const fri = new Date(mon);
	fri.setDate(fri.getDate() + 4);
	const opts = { day: "numeric", month: "short", year: "numeric" };
	if (mon.getMonth() === fri.getMonth()) {
		const startDay = new Intl.DateTimeFormat(locale, { day: "numeric" }).format(mon);
		const endFull = new Intl.DateTimeFormat(locale, opts).format(fri);
		return `${startDay}–${endFull}`;
	}
	return `${new Intl.DateTimeFormat(locale, { day: "numeric", month: "short" }).format(mon)} – ${new Intl.DateTimeFormat(locale, opts).format(fri)}`;
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

// Default empty modal state — cloned on open
const EMPTY_MODAL = {
	open: false,
	// mode: 'add' | 'edit'
	mode: "add",
	// pre-fill values
	allocationName: "", // existing record name (edit mode)
	employee: "",
	employeeFullName: "",
	day: "",
	project: "",
	hours: "8",
	notes: "",
	saving: false,
	deleting: false,
};

export const useCapacityPlanningStore = defineStore("capacityPlanning", () => {
	// ── State ──────────────────────────────────────────────────────────────
	const weekStart = ref(getMondayOf());
	const projectFilter = ref("");
	const employeeFilter = ref("");

	const planningData = ref(null);
	const projects = ref([]);

	const loading = ref(false);
	const error = ref(null);

	const modal = ref({ ...EMPTY_MODAL });

	// ── Computed ───────────────────────────────────────────────────────────

	const weekLabel = computed(() => formatWeekLabel(weekStart.value));
	const days = computed(() => planningData.value?.days ?? []);
	const employees = computed(() => planningData.value?.employees ?? []);
	const dailyCapacity = computed(() => planningData.value?.daily_capacity_hours ?? 8);
	const hasData = computed(() => planningData.value !== null);

	const selectedProject = computed(
		() => projects.value.find((p) => p.name === projectFilter.value) ?? null
	);

	// Unique sorted project list that has allocations this week (for legend / filter)
	const activeProjects = computed(() => {
		const seen = new Map();
		for (const emp of employees.value) {
			for (const day of days.value) {
				for (const alloc of emp.days[day]?.allocations ?? []) {
					if (!seen.has(alloc.project)) {
						seen.set(alloc.project, {
							project: alloc.project,
							project_name: alloc.project_name,
							color: alloc.color,
						});
					}
				}
			}
		}
		return [...seen.values()].sort((a, b) => a.project_name.localeCompare(b.project_name));
	});

	// ── Actions ────────────────────────────────────────────────────────────

	async function fetchData() {
		loading.value = true;
		error.value = null;
		try {
			const params = { week_start: weekStart.value };
			if (projectFilter.value) params.project = projectFilter.value;
			if (employeeFilter.value) params.employee_user = employeeFilter.value;

			planningData.value = await apiCall(
				"erpnext_projekt_hub.api.capacity_planning.get_capacity_planning_data",
				params
			);
		} catch (err) {
			error.value = err.message || "Failed to load capacity data";
			console.error("[CapacityPlanning] fetchData error:", err);
		} finally {
			loading.value = false;
		}
	}

	async function fetchProjects() {
		try {
			const data = await apiCall(
				"erpnext_projekt_hub.api.capacity_planning.get_capacity_projects",
				{}
			);
			projects.value = data ?? [];
		} catch (err) {
			console.error("[CapacityPlanning] fetchProjects error:", err);
		}
	}

	function prevWeek() {
		weekStart.value = shiftWeek(weekStart.value, -1);
	}

	function nextWeek() {
		weekStart.value = shiftWeek(weekStart.value, +1);
	}

	function goToCurrentWeek() {
		weekStart.value = getMondayOf();
	}

	function setProject(name) {
		projectFilter.value = name;
	}

	function setEmployee(user) {
		employeeFilter.value = user;
	}

	// ── Modal ──────────────────────────────────────────────────────────────

	function openAddModal({ employee, employeeFullName, day }) {
		modal.value = {
			...EMPTY_MODAL,
			open: true,
			mode: "add",
			employee,
			employeeFullName,
			day,
			project: projectFilter.value,
			hours: "8",
		};
	}

	function openEditModal({ allocation, employee, employeeFullName }) {
		modal.value = {
			...EMPTY_MODAL,
			open: true,
			mode: "edit",
			allocationName: allocation.name,
			employee,
			employeeFullName,
			day: allocation.day ?? modal.value.day,
			project: allocation.project,
			hours: String(allocation.hours),
			notes: allocation.notes ?? "",
		};
	}

	function closeModal() {
		modal.value = { ...EMPTY_MODAL };
	}

	async function saveModal() {
		const m = modal.value;
		if (!m.project || !m.employee || !m.day) return;

		m.saving = true;
		try {
			const params = {
				employee: m.employee,
				project: m.project,
				allocation_date: m.day,
				hours: parseFloat(m.hours) || 0,
				notes: m.notes,
			};
			if (m.mode === "edit" && m.allocationName) {
				params.name = m.allocationName;
			}

			await apiCall(
				"erpnext_projekt_hub.api.capacity_planning.save_allocation",
				params
			);

			if (window.frappe) {
				frappe.show_alert({
					message: m.mode === "edit" ? __("Allocation updated") : __("Allocation saved"),
					indicator: "green",
				});
			}
			closeModal();
			await fetchData();
		} catch (err) {
			if (window.frappe) {
				frappe.show_alert({ message: err.message || "Error", indicator: "red" });
			}
		} finally {
			m.saving = false;
		}
	}

	async function deleteAllocation(allocationName) {
		modal.value.deleting = true;
		try {
			await apiCall(
				"erpnext_projekt_hub.api.capacity_planning.delete_allocation",
				{ allocation_name: allocationName }
			);

			if (window.frappe) {
				frappe.show_alert({ message: __("Allocation deleted"), indicator: "green" });
			}
			closeModal();
			await fetchData();
		} catch (err) {
			if (window.frappe) {
				frappe.show_alert({ message: err.message || "Error", indicator: "red" });
			}
		} finally {
			modal.value.deleting = false;
		}
	}

	return {
		// state
		weekStart,
		projectFilter,
		employeeFilter,
		planningData,
		projects,
		loading,
		error,
		modal,
		// computed
		weekLabel,
		days,
		employees,
		dailyCapacity,
		hasData,
		selectedProject,
		activeProjects,
		// actions
		fetchData,
		fetchProjects,
		prevWeek,
		nextWeek,
		goToCurrentWeek,
		setProject,
		setEmployee,
		openAddModal,
		openEditModal,
		closeModal,
		saveModal,
		deleteAllocation,
	};
});
