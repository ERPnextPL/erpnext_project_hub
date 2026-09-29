import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { translate } from "../utils/translation";

const API = "erpnext_projekt_hub.api.work_planning";
const SHOW_WEEKEND_KEY = "projekt-hub:work-planning:show-weekend";

function getCsrfToken() {
	if (window.frappe && window.frappe.csrf_token && window.frappe.csrf_token !== "None") {
		return window.frappe.csrf_token;
	}
	if (window.csrf_token && window.csrf_token !== "{{ csrf_token }}") {
		return window.csrf_token;
	}
	return "";
}

function showAlert(message, indicator = "blue") {
	if (window.frappe?.show_alert) {
		window.frappe.show_alert({ message, indicator });
	}
}

function parseServerMessages(data) {
	if (!data._server_messages) return [];
	try {
		return JSON.parse(data._server_messages)
			.map((raw) => {
				try {
					const message = JSON.parse(raw);
					return { text: message.message, indicator: message.indicator };
				} catch (e) {
					return { text: raw };
				}
			})
			.filter((message) => message.text);
	} catch (e) {
		return [];
	}
}

async function apiCall(method, params = {}) {
	const formData = new FormData();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined) {
			formData.append(key, typeof value === "object" ? JSON.stringify(value) : value);
		}
	});

	const response = await fetch(`/api/method/${API}.${method}`, {
		method: "POST",
		headers: { "X-Frappe-CSRF-Token": getCsrfToken() },
		body: formData,
	});
	const data = await response.json();
	const messages = parseServerMessages(data);

	if (!response.ok) {
		const errorMessage =
			messages.map((message) => message.text).join(" ") ||
			data.exception ||
			translate("Something went wrong");
		showAlert(errorMessage, "red");
		throw new Error(errorMessage);
	}

	messages.forEach((message) => showAlert(message.text, message.indicator || "blue"));
	return data.message;
}

export function toISODate(date) {
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, "0");
	const day = String(date.getDate()).padStart(2, "0");
	return `${year}-${month}-${day}`;
}

export function parseISODate(value) {
	const [year, month, day] = value.split("-").map(Number);
	return new Date(year, month - 1, day);
}

function getMonday(date = new Date()) {
	const monday = new Date(date.getFullYear(), date.getMonth(), date.getDate());
	monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
	return monday;
}

export function isWeekend(isoDate) {
	const weekday = parseISODate(isoDate).getDay();
	return weekday === 0 || weekday === 6;
}

export function roundHours(hours) {
	return Math.round((hours + Number.EPSILON) * 100) / 100;
}

export function getLocale() {
	return window.frappe?.boot?.lang || window.lang || navigator.language || "pl";
}

export function formatHours(hours) {
	return Number(hours || 0).toLocaleString(getLocale(), { maximumFractionDigits: 2 });
}

export function formatDay(isoDate, options = { weekday: "short", day: "2-digit", month: "2-digit" }) {
	return new Intl.DateTimeFormat(getLocale(), options).format(parseISODate(isoDate));
}

// "empty" nothing planned, "partial" free time left, "full" fully planned, "over" above availability.
export function getLoadState(planned, available) {
	if (planned - available > 0.001) return "over";
	if (planned <= 0) return "empty";
	if (available - planned > 0.001) return "partial";
	return "full";
}

function readShowWeekend() {
	try {
		return window.localStorage.getItem(SHOW_WEEKEND_KEY) === "1";
	} catch (e) {
		return false;
	}
}

export const useWorkPlanningStore = defineStore("workPlanning", () => {
	const weekStart = ref(toISODate(getMonday()));
	const dates = ref([]);
	const employees = ref([]);
	const availability = ref({});
	const plan = ref({});
	const canPlan = ref(false);
	const departments = ref([]);
	const defaultDailyHours = ref(8);
	const loading = ref(false);
	const loaded = ref(false);
	const error = ref(null);

	const search = ref("");
	const department = ref("");
	const showWeekend = ref(readShowWeekend());

	const projectsCache = new Map();

	function getDay(employee, date) {
		return (
			availability.value[employee]?.[date] || {
				hours: 0,
				base_hours: defaultDailyHours.value,
				status: "work",
				reason: null,
				half_day: false,
			}
		);
	}

	function getEntries(employee, date) {
		return plan.value[employee]?.[date] || [];
	}

	function getPlanned(employee, date) {
		return roundHours(getEntries(employee, date).reduce((sum, entry) => sum + entry.hours, 0));
	}

	function getAvailable(employee, date) {
		return getDay(employee, date).hours || 0;
	}

	const filteredEmployees = computed(() => {
		const query = search.value.trim().toLowerCase();
		if (!query) return employees.value;
		return employees.value.filter((employee) =>
			[employee.employee_name, employee.name, employee.designation]
				.filter(Boolean)
				.some((value) => value.toLowerCase().includes(query))
		);
	});

	// Weekend days stay hidden unless asked for, or somebody works or is planned on them.
	const visibleDates = computed(() =>
		dates.value.filter(
			(date) =>
				!isWeekend(date) ||
				showWeekend.value ||
				employees.value.some(
					(employee) =>
						getAvailable(employee.name, date) > 0 ||
						getEntries(employee.name, date).length > 0
				)
		)
	);

	function getEmployeeWeek(employee) {
		let planned = 0;
		let available = 0;
		dates.value.forEach((date) => {
			planned += getPlanned(employee, date);
			available += getAvailable(employee, date);
		});
		return { planned: roundHours(planned), available: roundHours(available) };
	}

	function getDayTotals(date) {
		let planned = 0;
		let available = 0;
		filteredEmployees.value.forEach((employee) => {
			planned += getPlanned(employee.name, date);
			available += getAvailable(employee.name, date);
		});
		return { planned: roundHours(planned), available: roundHours(available) };
	}

	const weekTotals = computed(() => {
		let planned = 0;
		let available = 0;
		let overbooked = 0;
		filteredEmployees.value.forEach((employee) => {
			dates.value.forEach((date) => {
				const dayPlanned = getPlanned(employee.name, date);
				const dayAvailable = getAvailable(employee.name, date);
				planned += dayPlanned;
				available += dayAvailable;
				if (dayPlanned - dayAvailable > 0.001) overbooked += 1;
			});
		});
		return {
			planned: roundHours(planned),
			available: roundHours(available),
			free: roundHours(Math.max(available - planned, 0)),
			overbookedDays: overbooked,
		};
	});

	const projectSummary = computed(() => {
		const projects = new Map();
		filteredEmployees.value.forEach((employee) => {
			dates.value.forEach((date) => {
				getEntries(employee.name, date).forEach((entry) => {
					if (!projects.has(entry.project)) {
						projects.set(entry.project, {
							project: entry.project,
							project_name: entry.project_name || entry.project,
							hours: 0,
							employees: new Map(),
						});
					}
					const project = projects.get(entry.project);
					project.hours += entry.hours;
					project.employees.set(
						employee.name,
						roundHours((project.employees.get(employee.name) || 0) + entry.hours)
					);
				});
			});
		});

		return Array.from(projects.values())
			.map((project) => ({
				...project,
				hours: roundHours(project.hours),
				employees: Array.from(project.employees.entries())
					.map(([employee, hours]) => ({
						employee,
						employee_name:
							employees.value.find((row) => row.name === employee)?.employee_name ||
							employee,
						hours,
					}))
					.sort((a, b) => b.hours - a.hours),
			}))
			.sort((a, b) => b.hours - a.hours);
	});

	async function fetchPlan() {
		loading.value = true;
		error.value = null;
		try {
			const data = await apiCall("get_work_plan", {
				week_start: weekStart.value,
				department: department.value || null,
			});
			weekStart.value = data.week_start;
			dates.value = data.dates || [];
			employees.value = data.employees || [];
			availability.value = data.availability || {};
			plan.value = data.plan || {};
			canPlan.value = !!data.can_plan;
			departments.value = data.departments || [];
			defaultDailyHours.value = data.default_daily_hours || 8;
			loaded.value = true;
		} catch (err) {
			error.value = err.message || translate("Failed to load the work plan");
		} finally {
			loading.value = false;
		}
	}

	function shiftWeek(weeks) {
		const monday = parseISODate(weekStart.value);
		monday.setDate(monday.getDate() + weeks * 7);
		weekStart.value = toISODate(monday);
		return fetchPlan();
	}

	function goToCurrentWeek() {
		weekStart.value = toISODate(getMonday());
		return fetchPlan();
	}

	function goToDate(isoDate) {
		if (!isoDate) return;
		weekStart.value = toISODate(getMonday(parseISODate(isoDate)));
		return fetchPlan();
	}

	function setDepartment(value) {
		department.value = value || "";
		return fetchPlan();
	}

	function setShowWeekend(value) {
		showWeekend.value = !!value;
		try {
			window.localStorage.setItem(SHOW_WEEKEND_KEY, value ? "1" : "0");
		} catch (e) {
			// Only a convenience: the toggle still works for this visit.
		}
	}

	async function fetchProjects(employee) {
		const key = employee || "";
		if (!projectsCache.has(key)) {
			projectsCache.set(key, await apiCall("get_plannable_projects", { employee }));
		}
		return projectsCache.get(key);
	}

	function warnOverbooked(overbooked) {
		if (!overbooked?.length) return;
		const days = overbooked
			.map((day) => `${day.date} (${day.planned} / ${day.available} h)`)
			.join(", ");
		showAlert(translate("Planned above availability: {0}", [days]), "orange");
	}

	async function saveEntries({ employee, project, allocations, note }) {
		const result = await apiCall("save_plan_entries", { employee, project, allocations, note });
		showAlert(translate("Work plan saved"), "green");
		warnOverbooked(result?.overbooked);
		await fetchPlan();
		return result;
	}

	async function updateEntry({ name, hours, project, note }) {
		const result = await apiCall("update_plan_entry", { name, hours, project, note });
		showAlert(translate("Work plan saved"), "green");
		warnOverbooked(result?.overbooked);
		await fetchPlan();
		return result;
	}

	async function deleteEntry(name) {
		await apiCall("delete_plan_entry", { name });
		showAlert(translate("Plan entry deleted"), "green");
		await fetchPlan();
	}

	async function copyPreviousWeek() {
		const result = await apiCall("copy_previous_week", {
			week_start: weekStart.value,
			department: department.value || null,
		});
		const skipped = (result?.skipped_unavailable || 0) + (result?.skipped_planned || 0);
		showAlert(
			translate("Copied {0} entries from the previous week, skipped {1}", [
				result?.copied || 0,
				skipped,
			]),
			result?.copied ? "green" : "orange"
		);
		await fetchPlan();
		return result;
	}

	return {
		weekStart,
		dates,
		employees,
		availability,
		plan,
		canPlan,
		departments,
		defaultDailyHours,
		loading,
		loaded,
		error,
		search,
		department,
		showWeekend,
		filteredEmployees,
		visibleDates,
		weekTotals,
		projectSummary,
		getDay,
		getEntries,
		getPlanned,
		getAvailable,
		getEmployeeWeek,
		getDayTotals,
		fetchPlan,
		shiftWeek,
		goToCurrentWeek,
		goToDate,
		setDepartment,
		setShowWeekend,
		fetchProjects,
		saveEntries,
		updateEntry,
		deleteEntry,
		copyPreviousWeek,
	};
});
