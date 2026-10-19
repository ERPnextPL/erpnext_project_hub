import { ref, toValue } from "vue";
import { translate } from "../utils/translation";
import { apiPost, decodeApiError } from "../utils/customerRequests";
import { notifyRequestsChanged } from "../utils/requestsChannel";

const API = "erpnext_projekt_hub.api.project_hub";

/**
 * Changes made from the requests board: customer request workflow actions,
 * conversion, taking/releasing the analysis and saving it, and change request
 * workflow actions.
 *
 * Each call reports through `notify(message, kind)`, tells the other windows
 * about the change and awaits `refresh()`, so the request stays busy until the
 * refetched rows are on screen. Returns true when the change went through.
 */
export function useCustomerRequestActions(projectId, { refresh, notify }) {
	const busyRequest = ref("");

	async function run(request, method, payload, { success, failure }) {
		if (busyRequest.value) return false;

		busyRequest.value = request.name;
		try {
			const path = method.includes(".") ? method : `${API}.${method}`;
			const result = await apiPost(path, { name: request.name, ...payload });
			notify?.(success(result), "success");
			notifyRequestsChanged(toValue(projectId));
			await refresh?.();
			return true;
		} catch (err) {
			console.error(`Customer request ${method} failed:`, err);
			notify?.(decodeApiError(err, failure), "error");
			return false;
		} finally {
			busyRequest.value = "";
		}
	}

	function applyAction(request, action) {
		return run(
			request,
			"apply_customer_request_action",
			{ action },
			{
				success: (result) =>
					translate("{0} moved to {1}", [request.name, translate(result?.workflow_state || "")]),
				failure: translate("Status could not be changed"),
			}
		);
	}

	function applyChangeRequestAction(request, action) {
		return run(
			request,
			"apply_change_request_action",
			{ action },
			{
				success: (result) =>
					translate("{0} moved to {1}", [request.name, translate(result?.workflow_state || "")]),
				failure: translate("Status could not be changed"),
			}
		);
	}

	function createChangeRequest(request) {
		return run(
			request,
			"create_change_request_from_customer_request",
			{},
			{
				success: (result) => translate("Change request {0} created", [result?.change_request || ""]),
				failure: translate("Change request could not be created"),
			}
		);
	}

	// Customer and change requests share the analysis queue (request_queue.py).
	function takeRequest(request, doctype = "Customer Request") {
		return run(
			request,
			"erpnext_projekt_hub.request_queue.take_for_analysis",
			{ doctype },
			{
				success: () => translate("You are now analyzing {0}", [request.name]),
				failure: translate("Status could not be changed"),
			}
		);
	}

	function releaseRequest(request, doctype = "Customer Request") {
		return run(
			request,
			"erpnext_projekt_hub.request_queue.release_analysis",
			{ doctype },
			{
				success: () => translate("{0} is back in the analysis queue", [request.name]),
				failure: translate("Status could not be changed"),
			}
		);
	}

	function saveAnalysis(request, values) {
		return run(request, "update_customer_request_analysis", values, {
			success: () => translate("Analysis saved"),
			failure: translate("Analysis could not be saved"),
		});
	}

	return {
		busyRequest,
		applyAction,
		applyChangeRequestAction,
		createChangeRequest,
		takeRequest,
		releaseRequest,
		saveAnalysis,
	};
}
