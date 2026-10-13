/**
 * Shared helpers for Customer Request / Change Request views: the API calls,
 * workflow state metadata and display formatting used by the Requests tab and
 * the requests panel of the project view.
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
