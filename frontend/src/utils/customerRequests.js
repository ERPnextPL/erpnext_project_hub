/**
 * Shared helpers for Customer Request / Change Request views: the API calls,
 * workflow state metadata and display formatting used by the requests panel of
 * the project view and by the requests board.
 */

function getCsrfToken() {
	const win = typeof globalThis !== "undefined" ? globalThis.window : undefined;
	if (win?.frappe?.csrf_token && win.frappe.csrf_token !== "None") {
		return win.frappe.csrf_token;
	}
	if (win?.csrf_token && win.csrf_token !== "{{ csrf_token }}") {
		return win.csrf_token;
	}
	return "";
}

async function parseResponse(response) {
	const data = await response.json();
	if (!response.ok || data.exc) {
		const error = new Error(data.exception || data._server_messages || "API Error");
		error.status = response.status;
		throw error;
	}
	return data.message;
}

export async function apiGet(method, params = {}) {
	const query = new URLSearchParams(params);
	const response = await fetch(`/api/method/${method}?${query.toString()}`, {
		headers: {
			"X-Frappe-CSRF-Token": getCsrfToken(),
		},
	});
	return parseResponse(response);
}

export async function apiPost(method, payload = {}) {
	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: {
			"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
			"X-Frappe-CSRF-Token": getCsrfToken(),
		},
		body: new URLSearchParams(payload),
	});
	return parseResponse(response);
}

export function decodeApiError(error, fallback) {
	const raw = error?.message || "";
	if (!raw) return fallback;

	try {
		const parsed = JSON.parse(raw);
		if (Array.isArray(parsed)) {
			const messages = parsed
				.map((entry) => {
					try {
						const decoded = JSON.parse(entry);
						return decoded.message || decoded.title || entry;
					} catch {
						return entry;
					}
				})
				.filter(Boolean);
			if (messages.length > 0) {
				return messages.join(" ");
			}
		}
	} catch {
		// fall back to raw message
	}

	return raw.replace(/^Error:\s*/i, "") || fallback;
}

export function stripHtml(html) {
	if (!html) return "";
	return String(html)
		.replace(/<[^>]*>/g, " ")
		.replace(/&nbsp;/g, " ")
		.replace(/\s+/g, " ")
		.trim();
}

// Plain text of a Text Editor value that keeps its paragraph and line breaks.
export function htmlToText(html) {
	if (!html) return "";
	const withBreaks = String(html)
		.replace(/<br\s*\/?>/gi, "\n")
		.replace(/<\/(p|div|li|h[1-6])>/gi, "\n");
	const text =
		typeof DOMParser !== "undefined"
			? new DOMParser().parseFromString(withBreaks, "text/html").body.textContent || ""
			: withBreaks.replace(/<[^>]*>/g, "");
	return text.replace(/\n{3,}/g, "\n\n").trim();
}

export const REQUEST_SOURCES = ["Meeting", "Email", "Call", "Loop", "Other"];

// Customer Request Workflow states in pipeline order (see
// patches/post_model_sync/setup_customer_change_requests.py).
export const CUSTOMER_REQUEST_STATES = [
	"Draft",
	"To Analyze",
	"Quoted",
	"Accepted",
	"Converted",
	"Rejected",
];

// The happy path shown as a stage tracker; Rejected sits outside it.
export const CUSTOMER_REQUEST_PIPELINE = ["Draft", "To Analyze", "Quoted", "Accepted", "Converted"];

// States in which a request still needs work from the team.
export const OPEN_CUSTOMER_REQUEST_STATES = ["Draft", "To Analyze", "Quoted", "Accepted"];

const STATE_CLASSES = {
	Draft: "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200",
	"To Analyze": "bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200",
	Quoted: "bg-amber-50 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200",
	Accepted: "bg-green-50 text-green-700 dark:bg-green-900/40 dark:text-green-200",
	Converted: "bg-violet-50 text-violet-700 dark:bg-violet-900/40 dark:text-violet-200",
	Rejected: "bg-red-50 text-red-700 dark:bg-red-900/40 dark:text-red-200",
	Approved: "bg-green-50 text-green-700 dark:bg-green-900/40 dark:text-green-200",
	"Task Created": "bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200",
	Done: "bg-green-50 text-green-700 dark:bg-green-900/40 dark:text-green-200",
	Cancelled: "bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-300",
};

export function getRequestStateClass(state) {
	return STATE_CLASSES[state || "Draft"] || STATE_CLASSES.Draft;
}

export function isOpenCustomerRequest(request) {
	return OPEN_CUSTOMER_REQUEST_STATES.includes(request?.workflow_state || "Draft");
}

export function formatRequestAmount(row, amountField) {
	const amount = row[amountField];
	if (amount === null || amount === undefined || amount === "") return "-";
	return `${amount} ${row.currency || ""}`.trim();
}

export function deskUrl(doctype, name) {
	const route = doctype.toLowerCase().replaceAll(" ", "-");
	return name ? `/app/${route}/${encodeURIComponent(name)}` : `/app/${route}`;
}

// ---------------------------------------------------------------------------
// Requests board (kanban in its own window)
// ---------------------------------------------------------------------------

export const CONVERTED_STATE = "Converted";
export const REJECTED_STATE = "Rejected";

// Board columns in pipeline order. Closed columns start collapsed; the classes
// are spelled out in full so Tailwind keeps them.
export const REQUEST_BOARD_COLUMNS = [
	{
		state: "Draft",
		dot: "bg-gray-400",
		target: "border-gray-400 bg-gray-100",
		text: "text-gray-700",
	},
	{
		state: "To Analyze",
		dot: "bg-blue-500",
		target: "border-blue-500 bg-blue-50",
		text: "text-blue-800",
	},
	{
		state: "Quoted",
		dot: "bg-amber-500",
		target: "border-amber-500 bg-amber-50",
		text: "text-amber-800",
	},
	{
		state: "Accepted",
		dot: "bg-green-500",
		target: "border-green-500 bg-green-50",
		text: "text-green-800",
	},
	{
		state: CONVERTED_STATE,
		dot: "bg-violet-500",
		target: "border-violet-500 bg-violet-50",
		text: "text-violet-800",
		closed: true,
	},
	{
		state: REJECTED_STATE,
		dot: "bg-red-500",
		target: "border-red-500 bg-red-50",
		text: "text-red-800",
		closed: true,
	},
];

// A request that sits this many days in one of these states is flagged.
export const STALE_AFTER_DAYS = 7;
export const STALE_STATES = ["To Analyze", "Quoted"];

/**
 * Where the current user may move a request on the board, keyed by target
 * state: a workflow action, or the conversion into a Change Request (which has
 * no workflow transition on purpose, see apply_customer_request_action).
 */
export function getRequestMoves(request) {
	const moves = {};
	for (const action of request?.actions || []) {
		if (!moves[action.next_state]) {
			moves[action.next_state] = { type: "action", action: action.action };
		}
	}
	if (request?.can_create_change_request) {
		moves[CONVERTED_STATE] = { type: "convert", action: "Create Change Request" };
	}
	return moves;
}

/** Whole days the request has spent in its current workflow state. */
export function daysInState(request, now = new Date()) {
	const since = request?.state_changed_on || request?.modified;
	if (!since) return null;
	const start = new Date(String(since).replace(" ", "T"));
	if (Number.isNaN(start.getTime())) return null;
	const startDay = Date.UTC(start.getFullYear(), start.getMonth(), start.getDate());
	const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
	return Math.max(0, Math.round((today - startDay) / 86400000));
}

export function isStaleRequest(request, now = new Date()) {
	if (!STALE_STATES.includes(request?.workflow_state)) return false;
	const days = daysInState(request, now);
	return days !== null && days >= STALE_AFTER_DAYS;
}

export function isAssignedTo(request, user) {
	return Boolean(user) && (request?.assigned_to || []).some((assignee) => assignee.user === user);
}

/**
 * Board filters: free text, assignment (all / mine / unassigned), source and
 * request date period in days.
 */
export function filterBoardRequests(requests, filters, user, now = new Date()) {
	const query = String(filters?.q || "").trim().toLowerCase();
	const periodDays = Number(filters?.period) || 0;
	const periodStart = periodDays
		? Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) - periodDays * 86400000
		: null;

	return (requests || []).filter((request) => {
		if (filters?.assigned === "mine" && !isAssignedTo(request, user)) return false;
		if (filters?.assigned === "unassigned" && (request.assigned_to || []).length > 0) return false;
		if (filters?.source && request.source !== filters.source) return false;
		if (periodStart !== null) {
			const date = request.request_date ? Date.parse(`${request.request_date}T00:00:00Z`) : NaN;
			if (Number.isNaN(date) || date < periodStart) return false;
		}
		if (!query) return true;
		return [request.subject, request.name, request.requested_by_name, stripHtml(request.notes)].some(
			(value) => String(value || "").toLowerCase().includes(query)
		);
	});
}

function stateSince(request) {
	return String(request.state_changed_on || request.modified || "");
}

/**
 * Group requests into board columns. Open columns list the request waiting the
 * longest first; closed columns the latest first. States the board does not
 * know (a customised workflow) get a column of their own at the end.
 */
export function buildBoardColumns(requests) {
	const known = new Set(REQUEST_BOARD_COLUMNS.map((column) => column.state));
	const extraStates = [];
	for (const request of requests || []) {
		const state = request.workflow_state || "Draft";
		if (!known.has(state) && !extraStates.includes(state)) extraStates.push(state);
	}
	const columns = [
		...REQUEST_BOARD_COLUMNS,
		...extraStates.map((state) => ({
			state,
			dot: "bg-gray-400",
			target: "border-gray-400 bg-gray-100",
			text: "text-gray-700",
		})),
	];

	return columns.map((column) => {
		const items = (requests || []).filter((request) => (request.workflow_state || "Draft") === column.state);
		items.sort((a, b) =>
			column.closed
				? stateSince(b).localeCompare(stateSince(a))
				: stateSince(a).localeCompare(stateSince(b))
		);
		return {
			...column,
			requests: items,
			hours: items.reduce((total, request) => total + (Number(request.estimated_hours) || 0), 0),
			amounts: sumAmounts(items),
		};
	});
}

/** Estimated amounts summed per currency, e.g. [{ currency: "PLN", amount: 1200 }]. */
export function sumAmounts(requests) {
	const totals = new Map();
	for (const request of requests || []) {
		const amount = Number(request.estimated_amount) || 0;
		if (!amount) continue;
		const currency = request.currency || "";
		totals.set(currency, (totals.get(currency) || 0) + amount);
	}
	return [...totals.entries()].map(([currency, amount]) => ({ currency, amount }));
}

export function formatNumber(value, maximumFractionDigits = 2) {
	return Number(value || 0).toLocaleString("pl-PL", { maximumFractionDigits });
}

export function formatAmounts(amounts) {
	return (amounts || [])
		.map(({ currency, amount }) => `${formatNumber(amount)} ${currency}`.trim())
		.join(" · ");
}

export function requestsBoardPath(project) {
	return `/project-hub/${encodeURIComponent(project)}/requests-board`;
}

export function requestsBoardWindowName(project) {
	return `projekt-hub-requests-${project}`;
}

/**
 * Open the requests board of a project in its own browser window, or bring
 * that window to the front when it is already open (without reloading it, so
 * its filters stay). Returns false when the browser blocked the popup.
 */
export function openRequestsBoardWindow(project) {
	const win = typeof globalThis !== "undefined" ? globalThis.window : undefined;
	if (!win?.open || !project) return false;

	const path = requestsBoardPath(project);
	const boardWindow = win.open("", requestsBoardWindowName(project), "popup,width=1440,height=900");
	if (!boardWindow) return false;

	let showsBoard = false;
	try {
		showsBoard = boardWindow.location.pathname === path;
	} catch {
		showsBoard = false;
	}
	if (!showsBoard) boardWindow.location.href = path;
	boardWindow.focus?.();
	return true;
}

/**
 * Click handler of a link to the requests board: opens the board window, but
 * leaves a modified click (new tab) or a blocked popup to the link itself.
 */
export function openRequestsBoardFromLink(event, project) {
	if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) return;
	if (openRequestsBoardWindow(project)) event.preventDefault();
}
