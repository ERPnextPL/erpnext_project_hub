// Approval stage of time entries, mirroring erpnext_projekt_hub/timesheet_approval.py.
// A time entry belongs to a timesheet; the timesheet goes Draft -> Pending Approval ->
// Approved (or Rejected, then back to Pending Approval). Approved timesheets keep their
// billing status (Billed, Payslip, ...).

export const APPROVAL = Object.freeze({
	DRAFT: "Draft",
	PENDING: "Pending Approval",
	REJECTED: "Rejected",
	APPROVED: "Approved",
	CANCELLED: "Cancelled",
});

const BILLING_STATUSES = ["Partially Billed", "Billed", "Payslip", "Completed"];

// Badge colours per tone; full class names so Tailwind generates them.
const TONE_CLASSES = {
	gray: "bg-gray-100 text-gray-700",
	orange: "bg-orange-100 text-orange-800",
	red: "bg-red-100 text-red-800",
	green: "bg-emerald-100 text-emerald-800",
	blue: "bg-blue-100 text-blue-800",
};

/** Approval stage of the entry's timesheet. Without a workflow state the docstatus decides. */
export function getApprovalState(log) {
	if (log?.workflow_state) return log.workflow_state;
	if (Number(log?.docstatus) === 1) return APPROVAL.APPROVED;
	if (Number(log?.docstatus) === 2) return APPROVAL.CANCELLED;
	return APPROVAL.DRAFT;
}

/** Draft and rejected entries are still the employee's to change and to send. */
export function isEditableLog(log) {
	if (Number(log?.docstatus) !== 0) return false;
	const state = getApprovalState(log);
	return state === APPROVAL.DRAFT || state === APPROVAL.REJECTED;
}

export function isPendingLog(log) {
	return Number(log?.docstatus) === 0 && getApprovalState(log) === APPROVAL.PENDING;
}

export function isRejectedLog(log) {
	return Number(log?.docstatus) === 0 && getApprovalState(log) === APPROVAL.REJECTED;
}

export function isApprovedLog(log) {
	return Number(log?.docstatus) === 1;
}

/** Label (untranslated) and tone of the status badge. */
export function getApprovalBadge(log) {
	const state = getApprovalState(log);
	if (isApprovedLog(log)) {
		if (BILLING_STATUSES.includes(log?.status)) return { label: log.status, tone: "blue" };
		return { label: APPROVAL.APPROVED, tone: "green" };
	}
	if (state === APPROVAL.PENDING) return { label: state, tone: "orange" };
	if (state === APPROVAL.REJECTED) return { label: state, tone: "red" };
	if (state === APPROVAL.CANCELLED) return { label: state, tone: "gray" };
	return { label: APPROVAL.DRAFT, tone: "gray" };
}

export function getToneClasses(tone) {
	return TONE_CLASSES[tone] || TONE_CLASSES.gray;
}

function sumHours(logs) {
	return logs.reduce((sum, log) => sum + (parseFloat(log.hours) || 0), 0);
}

/** Hours and entry counts per approval stage. */
export function summarizeApproval(logs = []) {
	const toSend = logs.filter(isEditableLog);
	const rejected = logs.filter(isRejectedLog);
	const pending = logs.filter(isPendingLog);
	const approved = logs.filter(isApprovedLog);
	return {
		toSendHours: sumHours(toSend),
		toSendCount: toSend.length,
		rejectedHours: sumHours(rejected),
		rejectedCount: rejected.length,
		pendingHours: sumHours(pending),
		pendingCount: pending.length,
		approvedHours: sumHours(approved),
		approvedCount: approved.length,
	};
}

/** Timesheets of the given entries that can be sent for approval, with the hours they hold. */
export function timesheetsToSend(logs = []) {
	const names = new Set();
	let hours = 0;
	logs.filter(isEditableLog).forEach((log) => {
		if (!log.timesheet_name) return;
		names.add(log.timesheet_name);
		hours += parseFloat(log.hours) || 0;
	});
	return { timesheets: [...names], hours };
}

/** One entry per rejected timesheet, with the reason, for the "rejected" notice. */
export function rejectedTimesheets(logs = []) {
	const byTimesheet = new Map();
	logs.filter(isRejectedLog).forEach((log) => {
		const entry = byTimesheet.get(log.timesheet_name) || {
			timesheet: log.timesheet_name,
			reason: log.rejection_reason || "",
			reviewer: log.reviewed_by_name || log.reviewed_by || "",
			reviewedOn: log.reviewed_on || "",
			hours: 0,
			entries: 0,
		};
		entry.hours += parseFloat(log.hours) || 0;
		entry.entries += 1;
		byTimesheet.set(log.timesheet_name, entry);
	});
	return [...byTimesheet.values()];
}
