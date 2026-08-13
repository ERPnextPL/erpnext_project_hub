import { getStatusLabel } from "./taskStatus";

/**
 * Statuses of the Project Milestone doctype.
 *
 * These are deliberately NOT the Task statuses - a milestone has its own set,
 * which is why "In Progress" is valid here but never on a Task (a Task uses
 * "Working"). This is only the offline fallback for when `get_milestone_statuses`
 * can't be reached - the doctype's `status` field options are the source of truth.
 */
export const MILESTONE_STATUSES = ["Open", "In Progress", "Completed", "Cancelled"];

/** Localised label. The status value itself is the translation source string. */
export const getMilestoneStatusLabel = getStatusLabel;

export function isMilestoneCompleted(milestone) {
	return milestone.status === "Completed" || milestone.health === "completed";
}
