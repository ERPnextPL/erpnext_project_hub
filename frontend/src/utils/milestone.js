import { getStatusLabel } from "./taskStatus";

/** Localised label. The status value itself is the translation source string. */
export const getMilestoneStatusLabel = getStatusLabel;

export function isMilestoneCompleted(milestone) {
	return milestone.status === "Completed" || milestone.health === "completed";
}
