/**
 * Parent/subtask helpers working on a flat list of tasks (`name`, `parent_task`).
 */

/** Direct subtasks of a task. */
export function getChildren(tasks, taskName) {
	return (tasks || []).filter((task) => task.parent_task === taskName);
}

/** All subtasks of a task, at any depth. */
export function getDescendants(tasks, taskName) {
	const result = [];
	const visit = (name) => {
		for (const child of getChildren(tasks, name)) {
			result.push(child);
			visit(child.name);
		}
	};
	visit(taskName);
	return result;
}

/** Counts of direct subtasks: `{ total, done }`, where done means Completed. */
export function getSubtaskStats(tasks, taskName) {
	const children = getChildren(tasks, taskName);
	return {
		total: children.length,
		done: children.filter((task) => task.status === "Completed").length,
	};
}

/**
 * Cancel a task together with all of its subtasks, after asking the user.
 * `updateTask(name, updates)` applies one change (store action).
 * Returns false when the user declined.
 */
export async function cancelTaskWithSubtasks(tasks, task, updateTask, { translate, notify } = {}) {
	const t = translate || ((text) => text);
	const descendants = getDescendants(tasks, task.name);
	const subtaskCount = descendants.length;

	if (subtaskCount > 0) {
		const confirmed = window.confirm(
			t(
				`This task has {subtaskCount} subtasks.\n\n` +
					`Cancelling this task will also cancel all subtasks.\n\n` +
					`Do you want to continue?`,
				{ subtaskCount }
			)
		);
		if (!confirmed) return false;
	}

	await updateTask(task.name, { status: "Cancelled" });
	for (const subtask of descendants) {
		await updateTask(subtask.name, { status: "Cancelled" });
	}

	if (subtaskCount > 0) {
		notify?.(t("Task and {subtaskCount} subtasks cancelled", { subtaskCount }), "orange");
	}
	return true;
}
