export function isMilestoneCompleted(milestone) {
	return milestone.status === "Completed" || milestone.health === "completed";
}
