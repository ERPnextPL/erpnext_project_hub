import { getStatusLabel } from "./taskStatus";

/** Statuses of the Project Milestone doctype. */
export const MILESTONE_STATUSES = ["Open", "In Progress", "Completed", "Cancelled"];

/** Localised label. The status value itself is the translation source string. */
export const getMilestoneStatusLabel = getStatusLabel;

export function isMilestoneCompleted(milestone) {
	return milestone.status === "Completed" || milestone.health === "completed";
}

export const DEFAULT_MILESTONE_COLOR = "#3b82f6";

/**
 * Milestone label of a task: `{ name, label, color }`, or null when the task has
 * no milestone. Looks the milestone up in `milestones` (project views) and falls
 * back to `milestone_name` / `milestone_color` sent with the task (My Tasks).
 */
export function getTaskMilestone(task, milestones = []) {
	if (!task?.milestone) return null;
	const milestone = (milestones || []).find((item) => item.name === task.milestone);
	return {
		name: task.milestone,
		label: milestone?.milestone_name || task.milestone_name || task.milestone,
		color: milestone?.color || task.milestone_color || DEFAULT_MILESTONE_COLOR,
	};
}
