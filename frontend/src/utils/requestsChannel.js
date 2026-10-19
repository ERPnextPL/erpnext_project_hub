/**
 * Tells the other Projekt HUB windows of this browser that the customer
 * requests of a project changed, so the project view and the requests board
 * (opened in its own window) refetch instead of showing stale columns.
 *
 * A BroadcastChannel never delivers a message back to the instance that posted
 * it, and every window keeps a single instance, so a window is not woken by
 * its own changes.
 */

const CHANNEL_NAME = "projekt-hub-customer-requests";

let channel = null;

function getChannel() {
	if (typeof BroadcastChannel === "undefined") return null;
	if (!channel) channel = new BroadcastChannel(CHANNEL_NAME);
	return channel;
}

export function notifyRequestsChanged(project) {
	if (!project) return;
	getChannel()?.postMessage({ type: "requests-changed", project });
}

/** Call `callback(project)` whenever another window changed a project's requests. */
export function onRequestsChanged(callback) {
	const current = getChannel();
	if (!current) return () => {};

	const handler = (event) => {
		if (event.data?.type === "requests-changed") callback(event.data.project);
	};
	current.addEventListener("message", handler);
	return () => current.removeEventListener("message", handler);
}
