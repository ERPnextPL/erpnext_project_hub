import { computed, ref, toValue, watch } from "vue";
import { translate } from "../utils/translation";
import { apiGet, isOpenCustomerRequest } from "../utils/customerRequests";

/**
 * Customer and change requests of one project, refetched when the project
 * changes. `available` turns false when the user may not read requests, so the
 * caller can hide the entry point instead of showing a permission error.
 */
export function useProjectRequests(projectId) {
	const customerRequests = ref([]);
	const changeRequests = ref([]);
	const loading = ref(false);
	const error = ref("");
	const available = ref(true);
	let requestId = 0;
	let loadedProject = "";

	const openCount = computed(() => customerRequests.value.filter(isOpenCustomerRequest).length);

	async function fetchRequests() {
		const project = toValue(projectId);
		const currentRequest = ++requestId;
		// Rows of the previous project must never show under this one, even if
		// this fetch fails; a refresh of the same project keeps them meanwhile.
		if (project !== loadedProject) {
			customerRequests.value = [];
			changeRequests.value = [];
			loadedProject = project || "";
		}
		if (!project) {
			loading.value = false;
			return;
		}

		loading.value = true;
		error.value = "";
		try {
			const result = await apiGet("erpnext_projekt_hub.api.project_hub.get_project_requests", {
				project,
			});
			if (currentRequest !== requestId) return;
			customerRequests.value = result?.customer_requests || [];
			changeRequests.value = result?.change_requests || [];
			available.value = true;
		} catch (err) {
			if (currentRequest !== requestId) return;
			console.error("Failed to fetch project requests:", err);
			if (err?.status === 403) {
				available.value = false;
			}
			error.value = translate("Project requests failed to load");
		} finally {
			if (currentRequest === requestId) {
				loading.value = false;
			}
		}
	}

	watch(() => toValue(projectId), fetchRequests, { immediate: true });

	return {
		customerRequests,
		changeRequests,
		loading,
		error,
		available,
		openCount,
		fetchRequests,
	};
}
