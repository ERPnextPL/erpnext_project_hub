import { translate } from "./translation";

/**
 * Statuses of the Project Milestone doctype.
 *
 * These are deliberately NOT the Task statuses - a milestone has its own set,
 * which is why "In Progress" is valid here but never on a Task (a Task uses
 * "Working"). Keep in sync with the `status` field options of Project Milestone.
 */
export const MILESTONE_STATUSES = ["Open", "In Progress", "Completed", "Cancelled"];

/** Localised label. The status value itself is the translation source string. */
export function getMilestoneStatusLabel(status) {
	return status ? translate(status) : "";
}

export function isMilestoneCompleted(milestone) {
	return milestone.status === "Completed" || milestone.health === "completed";
}
