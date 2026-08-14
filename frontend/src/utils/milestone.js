import { getStatusLabel } from "./taskStatus";

/** Statuses of the Project Milestone doctype. */
export const MILESTONE_STATUSES = ["Open", "In Progress", "Completed", "Cancelled"];

/** Localised label. The status value itself is the translation source string. */
export const getMilestoneStatusLabel = getStatusLabel;

export function isMilestoneCompleted(milestone) {
	return milestone.status === "Completed" || milestone.health === "completed";
}
