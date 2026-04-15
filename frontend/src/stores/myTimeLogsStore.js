import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { translate } from "../utils/translation";

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
	const csrfToken = getCsrfToken();

	const formData = new FormData();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined && value !== "") {
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

export const useMyTimeLogsStore = defineStore("myTimeLogs", () => {
	const timelogs = ref([]);
	const loading = ref(false);
	const error = ref(null);
	const total = ref(0);

	const filters = ref({
		search: "",
		status: "",
		project: "",
		activityType: "",
		startDate: "",
		endDate: "",
	});
	const projectChoices = ref([]);

	const hasActiveFilters = computed(() => {
		return (
			!!filters.value.search ||
			!!filters.value.status ||
			!!filters.value.project ||
			!!filters.value.activityType ||
			!!filters.value.startDate ||
			!!filters.value.endDate
		);
	});

	async function fetchLogs() {
		loading.value = true;
		error.value = null;

		try {
			const params = {};
			if (filters.value.search) params.search = filters.value.search;
			if (filters.value.status) params.status = filters.value.status;
			if (filters.value.project) params.project = filters.value.project;
			if (filters.value.activityType) params.activity_type = filters.value.activityType;
			if (filters.value.startDate) params.start_date = filters.value.startDate;
			if (filters.value.endDate) params.end_date = filters.value.endDate;

			const data = await apiCall("erpnext_projekt_hub.api.project_hub.get_my_timelogs", params);
			timelogs.value = data?.timelogs || [];
			total.value = data?.total || timelogs.value.length;
		} catch (err) {
			error.value = err.message || translate("Failed to fetch time logs");
			console.error("Failed to fetch time logs:", err);
		} finally {
			loading.value = false;
		}
	}

	function setFilter(key, value) {
		if (Object.prototype.hasOwnProperty.call(filters.value, key)) {
			filters.value[key] = value;
		}
	}

	function resetFilters() {
		filters.value = {
			search: "",
			status: "",
			project: "",
			activityType: "",
			startDate: "",
			endDate: "",
		};
	}

	async function fetchProjectChoices() {
		try {
			const data = await apiCall("erpnext_projekt_hub.api.project_hub.get_my_tasks_projects", {});
			projectChoices.value = data || [];
	} catch (err) {
			console.error(translate("Failed to fetch project choices:"), err);
			projectChoices.value = [];
		}
	}

	async function updateTimelog(timelogName, updates) {
		const data = await apiCall("erpnext_projekt_hub.api.project_hub.update_timelog", {
			timelog_name: timelogName,
			...updates,
		});
		return data;
	}

	async function deleteTimelog(timelogName) {
		try {
			await apiCall("erpnext_projekt_hub.api.project_hub.delete_timelog", {
				timelog_name: timelogName,
			});
			await fetchLogs();
			return true;
		} catch (error) {
			console.error(translate("Failed to delete time log:"), error);
			throw error;
		}
	}

	return {
		timelogs,
		loading,
		error,
		total,
		filters,
		projectChoices,
		hasActiveFilters,
		fetchLogs,
		fetchProjectChoices,
		setFilter,
		resetFilters,
		updateTimelog,
		deleteTimelog,
	};
});
