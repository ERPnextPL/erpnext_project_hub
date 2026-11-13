<script setup>
import { ref } from "vue";
import { useTaskStore } from "../stores/taskStore";
import { getStatusLabel } from "../utils/taskStatus";
import { cancelTaskWithSubtasks, getDescendants } from "../utils/taskHierarchy";
import { getRealWindow, translate } from "../utils/translation";
import TaskBoard from "./organisms/TaskBoard.vue";
import TimeLogModal from "./TimeLogModal.vue";

/**
 * Project board: connects the shared TaskBoard to the project task store.
 */
const props = defineProps({
	tasks: {
		type: Array,
		required: true,
	},
	projectId: {
		type: String,
		required: true,
	},
	visibleStatuses: {
		type: Array,
		default: null,
	},
});

const emit = defineEmits(["task-click"]);

const store = useTaskStore();
const realWindow = getRealWindow();
const timeLogTask = ref(null);

function notify(message, indicator = "green") {
	realWindow?.frappe?.show_alert({ message, indicator });
}

function notifyError(error, fallback) {
	notify(error?.message || translate(fallback), "red");
}

async function moveTask(task, status) {
	try {
		if (status === "Cancelled") {
			// The board holds only filtered tasks: cascade over the full tree.
			const allTasks = await store.fetchAllProjectTasks(props.projectId);
			const done = await cancelTaskWithSubtasks(allTasks, task, store.updateTask, {
				translate,
				notify,
			});
			if (done) notify(translate("Task moved to {0}", [getStatusLabel(status)]));
			return done;
		}
		const result = await store.updateTask(task.name, { status });
		if (result?.status === status) {
			notify(translate("Task moved to {0}", [getStatusLabel(status)]));
		}
		return result;
	} catch (error) {
		notifyError(error, "Failed to update task");
		throw error;
	}
}

async function createTask({ subject, status }) {
	try {
		await store.createTask({ subject, project: props.projectId, status });
	} catch (error) {
		notifyError(error, "Failed to create task. Please try again.");
		throw error;
	}
}

async function loadColumnTasks(status) {
	if (status !== "Completed") return [];
	try {
		return await store.fetchCompletedProjectTasks(props.projectId);
	} catch (error) {
		notifyError(error, "Failed to fetch completed tasks");
		return [];
	}
}

async function updateTask(task, fields) {
	try {
		await store.updateTask(task.name, fields);
	} catch (error) {
		notifyError(error, "Failed to update task");
	}
}

async function assignMe(task) {
	const user = realWindow?.frappe?.session?.user;
	if (!user) return;
	try {
		await store.assignTask(task.name, user, "add");
		notify(translate("User assigned"));
	} catch (error) {
		notifyError(error, "Failed to update task");
	}
}

async function deleteTask(task) {
	try {
		// Ask about subtasks hidden by the filters too: deleting removes them all.
		const allTasks = await store.fetchAllProjectTasks(props.projectId);
		const message = getDescendants(allTasks, task.name).length
			? translate("This task has subtasks. Delete all subtasks as well?")
			: translate("Delete this task?");
		if (!realWindow?.confirm(message)) return;
		await store.deleteTask(task.name);
	} catch (error) {
		notifyError(error, "Failed to delete task");
	}
}

async function saveTimeLog(timelogData) {
	try {
		await store.createTimelog(timelogData);
		timeLogTask.value = null;
		notify(translate("Time log saved successfully"));
	} catch {
		notify(translate("Failed to save time log"), "red");
	}
}
</script>

<template>
	<div class="h-[calc(100vh-180px)] min-h-[28rem]">
		<TaskBoard
			:tasks="tasks"
			:all-tasks="store.tasks"
			:statuses="visibleStatuses || []"
			:users="store.availableUsers"
			:milestones="store.milestones"
			:priorities="store.taskPriorities.length ? store.taskPriorities : undefined"
			:column-counts="{ Completed: store.project?.completed_tasks }"
			:load-column-tasks="loadColumnTasks"
			:move-task="moveTask"
			:create-task="createTask"
			:storage-key="`projekt-hub:board-collapsed:${projectId}`"
			can-delete
			@open="(task) => emit('task-click', task)"
			@update="updateTask"
			@assign-me="assignMe"
			@log-time="(task) => (timeLogTask = task)"
			@delete="deleteTask"
		/>

		<TimeLogModal
			v-if="timeLogTask"
			:task="timeLogTask"
			:show="true"
			@close="timeLogTask = null"
			@save="saveTimeLog"
		/>
	</div>
</template>
