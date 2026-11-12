import { getRealWindow, translate } from "./translation";

const DAY_MS = 24 * 60 * 60 * 1000;

function startOfDay(value) {
	const date = value instanceof Date ? new Date(value) : new Date(`${value}T00:00:00`);
	date.setHours(0, 0, 0, 0);
	return date;
}

/**
 * Due-date state of a task, used by the due date badge in every task view.
 *
 * tone: "done" (task completed), "overdue", "today", "soon" (within 3 days),
 * "normal" or "none" (no due date).
 */
export function getDueState(task, now = new Date()) {
	const dateStr = task?.exp_end_date;
	if (!dateStr) return { tone: "none", label: "", daysLeft: null };

	const due = startOfDay(dateStr);
	if (Number.isNaN(due.getTime())) return { tone: "none", label: "", daysLeft: null };

	const daysLeft = Math.round((due - startOfDay(now)) / DAY_MS);
	const label = formatDueLabel(due, daysLeft);

	if (task.status === "Completed") return { tone: "done", label, daysLeft };
	if (task.is_overdue || daysLeft < 0) return { tone: "overdue", label, daysLeft };
	if (daysLeft === 0) return { tone: "today", label, daysLeft };
	if (daysLeft <= 3) return { tone: "soon", label, daysLeft };
	return { tone: "normal", label, daysLeft };
}

function formatDueLabel(due, daysLeft) {
	if (daysLeft === 0) return translate("Today");
	if (daysLeft === 1) return translate("Tomorrow");
	const lang = getRealWindow()?.frappe?.boot?.lang || "pl";
	const sameYear = due.getFullYear() === new Date().getFullYear();
	return due.toLocaleDateString(lang, {
		day: "numeric",
		month: "short",
		...(sameYear ? {} : { year: "numeric" }),
	});
}
