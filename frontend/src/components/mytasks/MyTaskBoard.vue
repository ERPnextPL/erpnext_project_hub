<script setup>
import { computed } from "vue";
import { useMyTasksStore } from "../../stores/myTasksStore";
import { ACTIVE_STATUSES, getStatusLabel } from "../../utils/taskStatus";
import { getRealWindow, translate } from "../../utils/translation";
import TaskBoard from "../organisms/TaskBoard.vue";
import KanbanAttentionPanel from "../KanbanAttentionPanel.vue";
import { useBoardTaskFocus } from "../../composables/useBoardTaskFocus";

/**
 * My Tasks board: the same TaskBoard as in a project, connected to the
 * My Tasks store. Cards show their project since tasks come from many projects.
 */
const emit = defineEmits(["log-time"]);

const store = useMyTasksStore();
const realWindow = getRealWindow();
const { highlightedTaskName, focusBoardTask } = useBoardTaskFocus();

function notify(message, indicator = "green") {
	realWindow?.frappe?.show_alert({ message, indicator });
}

// Without a status filter the API returns only open tasks, so list just those.
const statuses = computed(() =>
	store.filters.status.length ? store.filters.status : ACTIVE_STATUSES
);

// New cards need a project: offered only while the list is narrowed to one.
const canCreate = computed(() => Boolean(store.filters.project));

async function moveTask(task, status) {
	try {
		const result = await store.quickUpdateTask(task.name, { status });
		if (result?.status === status) {
			notify(translate("Task moved to {0}", [getStatusLabel(status)]));
		}
		return result;
	} catch (error) {
		notify(error?.message || translate("Failed to update task"), "red");
		throw error;
	}
}

async function createTask({ subject, status }) {
	await store.createTask({ subject, project: store.filters.project, status });
}

async function updateTask(task, fields) {
	try {
		await store.quickUpdateTask(task.name, fields);
	} catch (error) {
		notify(error?.message || translate("Failed to update task"), "red");
	}
}
</script>

<template>
	<p
		v-if="store.total > store.tasks.length"
		class="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800"
	>
		{{
			translate("Showing {0} of {1} tasks. Narrow the filters to see the rest.", [
				store.tasks.length,
				store.total,
			])
		}}
	</p>
	<div class="-mx-4 flex h-[calc(100vh-170px)] min-h-[28rem] sm:-mx-6 lg:-mx-8">
		<div class="h-full min-w-0 flex-1">
		<TaskBoard
			:tasks="store.tasks"
			:statuses="statuses"
			:users="store.users"
			:priorities="store.priorities.length ? store.priorities : undefined"
			:move-task="moveTask"
			:create-task="canCreate ? createTask : null"
			:can-assign-me="false"
			storage-key="projekt-hub:board-collapsed:my-tasks"
			show-project
			@open="(task) => store.selectTask(task)"
			@update="updateTask"
			@log-time="(task) => emit('log-time', task)"
		/>
		</div>
		<KanbanAttentionPanel
			class="hidden md:flex"
			:tasks="store.tasks"
			:highlighted-task="highlightedTaskName"
			:exclude="['unassigned']"
			@focus-task="focusBoardTask"
		/>
	</div>
</template>
