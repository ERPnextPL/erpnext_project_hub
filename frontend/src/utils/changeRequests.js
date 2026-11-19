/**
 * Change Request side of the requests board: columns, moves and filters. A
 * Change Request is what the customer approved; approving it creates the
 * project task, so it goes Draft -> Task Created -> Done (or Cancelled).
 */
import { daysInState, getRequestMoves, stripHtml } from "./customerRequests";

// Approved lasts only until the task exists, so it shares the Task Created column.
export const CHANGE_REQUEST_STATE_ALIASES = { Approved: "Task Created" };

export const CHANGE_REQUEST_BOARD_COLUMNS = [
	{
		state: "Draft",
		dot: "bg-gray-400",
		target: "border-gray-400 bg-gray-100",
		text: "text-gray-700",
	},
	{
		state: "Task Created",
		states: ["Approved", "Task Created"],
		dot: "bg-blue-500",
		target: "border-blue-500 bg-blue-50",
		text: "text-blue-800",
	},
	{
		state: "Done",
		dot: "bg-green-500",
		target: "border-green-500 bg-green-50",
		text: "text-green-800",
		closed: true,
	},
	{
		state: "Cancelled",
		dot: "bg-gray-500",
		target: "border-gray-500 bg-gray-100",
		text: "text-gray-700",
		closed: true,
	},
];

export const OPEN_CHANGE_REQUEST_STATES = ["Draft", "Approved", "Task Created"];

// A change request waiting this many days for approval is flagged.
export const CHANGE_REQUEST_STALE_AFTER_DAYS = 7;

export function isOpenChangeRequest(request) {
	return OPEN_CHANGE_REQUEST_STATES.includes(request?.workflow_state || "Draft");
}

export function getChangeRequestMoves(request) {
	return getRequestMoves(request, CHANGE_REQUEST_STATE_ALIASES);
}

export function isStaleChangeRequest(request, now = new Date()) {
	if ((request?.workflow_state || "Draft") !== "Draft") return false;
	const days = daysInState(request, now);
	return days !== null && days >= CHANGE_REQUEST_STALE_AFTER_DAYS;
}

/** Board filters of change requests: free text and creation period in days. */
export function filterChangeRequests(requests, filters, now = new Date()) {
	const query = String(filters?.q || "").trim().toLowerCase();
	const periodDays = Number(filters?.period) || 0;
	const periodStart = periodDays
		? Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) - periodDays * 86400000
		: null;

	return (requests || []).filter((request) => {
		if (periodStart !== null) {
			const created = Date.parse(`${String(request.creation || "").slice(0, 10)}T00:00:00Z`);
			if (Number.isNaN(created) || created < periodStart) return false;
		}
		if (!query) return true;
		return [
			request.subject,
			request.name,
			request.customer_request,
			request.task,
			stripHtml(request.approved_scope),
		].some((value) => String(value || "").toLowerCase().includes(query));
	});
}
