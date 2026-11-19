import { computed, getCurrentScope, onScopeDispose, ref, toValue, watch } from "vue";
import { translate } from "../utils/translation";
import { apiGet, isOpenCustomerRequest } from "../utils/customerRequests";
import { onRequestsChanged } from "../utils/requestsChannel";

/**
 * Customer and change requests of one project, refetched when the project
 * changes and when another window (the requests board) reports a change.
 * `available` turns false when the user may not read requests, so the caller
 * can hide the entry point instead of showing a permission error.
 */
export function useProjectRequests(projectId) {
	const customerRequests = ref([]);
	const changeRequests = ref([]);
	const project = ref(null);
	const lastLoadedAt = ref(null);
	const loading = ref(false);
	const error = ref("");
	const available = ref(true);
	let requestId = 0;
	let loadedProject = "";

	const openCount = computed(() => customerRequests.value.filter(isOpenCustomerRequest).length);

	async function fetchRequests() {
		const projectName = toValue(projectId);
		const currentRequest = ++requestId;
		// Rows of the previous project must never show under this one, even if
		// this fetch fails; a refresh of the same project keeps them meanwhile.
		if (projectName !== loadedProject) {
			customerRequests.value = [];
			changeRequests.value = [];
			project.value = null;
			lastLoadedAt.value = null;
			loadedProject = projectName || "";
		}
		if (!projectName) {
			loading.value = false;
			return false;
		}

		loading.value = true;
		error.value = "";
		try {
			const result = await apiGet("erpnext_projekt_hub.api.project_hub.get_project_requests", {
				project: projectName,
			});
			if (currentRequest !== requestId) return false;
			customerRequests.value = result?.customer_requests || [];
			changeRequests.value = result?.change_requests || [];
			project.value = result?.project || null;
			lastLoadedAt.value = new Date();
			available.value = true;
			return true;
		} catch (err) {
			if (currentRequest !== requestId) return false;
			console.error("Failed to fetch project requests:", err);
			if (err?.status === 403) {
				available.value = false;
			}
			error.value = translate("Project requests failed to load");
			return false;
		} finally {
			if (currentRequest === requestId) {
				loading.value = false;
			}
		}
	}

	watch(() => toValue(projectId), fetchRequests, { immediate: true });

	const stopListening = onRequestsChanged((changedProject) => {
		if (changedProject && changedProject === toValue(projectId)) fetchRequests();
	});
	if (getCurrentScope()) onScopeDispose(stopListening);

	return {
		customerRequests,
		changeRequests,
		project,
		lastLoadedAt,
		loading,
		error,
		available,
		openCount,
		fetchRequests,
	};
}
