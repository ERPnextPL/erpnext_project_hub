/**
 * Cards a TaskBoard loads itself (loadColumnTasks), kept per list in a Map
 * status -> tasks. The board's owner does not hold these records, so the board
 * must keep them in step with the moves it saves.
 */

/** After a saved move, give the loaded card its new status (and the saved fields). */
export function applyMoveToLoaded(loadedByStatus, taskName, status, result) {
	const saved = result?.status ?? (result ? status : null);
	if (!saved) return;
	for (const [listStatus, loaded] of loadedByStatus) {
		if (!loaded.some((task) => task.name === taskName)) continue;
		loadedByStatus.set(
			listStatus,
			loaded.map((task) => (task.name === taskName ? { ...task, ...(result || {}), status: saved } : task))
		);
	}
}

/**
 * Cards of one list: the owner's tasks with that status, plus loaded cards of
 * any list now carrying it - unless the owner already holds a fresher copy.
 */
export function cardsForStatus(ownerTasks, loadedByStatus, status, statusOf = (task) => task.status) {
	const cards = new Map(ownerTasks.filter((task) => statusOf(task) === status).map((task) => [task.name, task]));
	const owned = new Set(ownerTasks.map((task) => task.name));
	for (const loaded of loadedByStatus.values()) {
		for (const task of loaded) {
			if (!owned.has(task.name) && statusOf(task) === status) cards.set(task.name, task);
		}
	}
	return [...cards.values()];
}
