import { defineStore } from "pinia";
import { ref } from "vue";

function getCsrfToken() {
	if (window.frappe && window.frappe.csrf_token && window.frappe.csrf_token !== "None") {
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
		if (value !== null && value !== undefined && value !== "") formData.append(key, value);
	});

	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: { "X-Frappe-CSRF-Token": getCsrfToken() },
		body: formData,
	});
	const data = await response.json();
	if (!response.ok) {
		const error = data.exception || data._server_messages || "API Error";
		if (window.frappe) frappe.show_alert({ message: error, indicator: "red" });
		throw new Error(error);
	}
	return data.message;
}

export const useTimesheetApprovalStore = defineStore("timesheetApproval", () => {
	const items = ref([]);
	const projects = ref([]);
	const employees = ref([]);
	const total = ref(0);
	const totalHours = ref(0);
	const loading = ref(false);
	const error = ref("");

	async function fetchQueue(filters = {}) {
		loading.value = true;
		error.value = "";
		try {
			const data = await apiCall("erpnext_projekt_hub.api.project_hub.get_timesheets_to_approve", filters);
			items.value = data?.items || [];
			projects.value = data?.projects || [];
			employees.value = data?.employees || [];
			total.value = data?.total || 0;
			totalHours.value = data?.total_hours || 0;
		} catch (err) {
			error.value = err.message || "Failed to load approval queue";
		} finally {
			loading.value = false;
		}
	}

	async function approve(timesheet) {
		return apiCall("erpnext_projekt_hub.api.project_hub.approve_timesheet_for_project_manager", {
			timesheet,
		});
	}

	async function reject(timesheet, reason) {
		return apiCall("erpnext_projekt_hub.timesheet_approval.reject_timesheet", {
			timesheet,
			reason,
		});
	}

	return { items, projects, employees, total, totalHours, loading, error, fetchQueue, approve, reject };
});
