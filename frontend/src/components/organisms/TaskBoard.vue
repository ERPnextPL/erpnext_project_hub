<script setup>
import { computed, reactive, ref, watch } from "vue";
import TaskBoardColumn from "./TaskBoardColumn.vue";
import TaskQuickMenu from "../molecules/TaskQuickMenu.vue";
import { BOARD_STATUSES, getStatusConfig, getStatusLabel } from "../../utils/taskStatus";
import { getSubtaskStats } from "../../utils/taskHierarchy";
import { getTaskMilestone } from "../../utils/milestone";

/**
 * Trello-like board of tasks, one list per status. Store-agnostic: it receives
 * tasks and callbacks, so the project board and My Tasks share it.
 */
const props = defineProps({
	tasks: {
		type: Array,
		required: true,
	},
	// Statuses shown as lists. Empty means every board status.
	statuses: {
		type: Array,
		default: () => [],
	},
	// Statuses always offered as (collapsed) drop targets even when filtered out,
	// so a card can be completed by dragging it, like moving it to "Done".
	dropStatuses: {
		type: Array,
		default: () => ["Completed"],
	},
	// Tasks used to resolve parents and subtasks (defaults to `tasks`).
	allTasks: {
		type: Array,
		default: null,
	},
	users: {
		type: Array,
		default: () => [],
	},
	milestones: {
		type: Array,
		default: () => [],
	},
	priorities: {
		type: Array,
		default: () => ["Low", "Medium", "High", "Urgent"],
	},
	showProject: {
		type: Boolean,
		default: false,
	},
	// Async function(task, status) applying a status change. Returning a falsy
	// value (e.g. a cancelled completion prompt) puts the card back.
	moveTask: {
		type: Function,
		required: true,
	},
	// Async function({ subject, status }) - enables "Add task" in every list.
	createTask: {
		type: Function,
		default: null,
	},
	canDelete: {
		type: Boolean,
		default: false,
	},
	canLogTime: {
		type: Boolean,
		default: true,
	},
	canAssignMe: {
		type: Boolean,
		default: true,
	},
	// localStorage key remembering collapsed lists.
	storageKey: {
		type: String,
		default: "",
	},
});

const emit = defineEmits(["open", "update", "assign-me", "log-time", "delete"]);

// Status shown for a card while its move is being saved.
const pendingStatus = reactive(new Map());
const dragging = ref(false);
const menu = ref(null); // { task, anchor }

const hierarchy = computed(() => props.allTasks || props.tasks);
const taskByName = computed(() => new Map(hierarchy.value.map((task) => [task.name, task])));

const listedStatuses = computed(() => {
	const selected = props.statuses?.length ? props.statuses : BOARD_STATUSES;
	return BOARD_STATUSES.filter((status) => selected.includes(status));
});

// --- collapsed lists (remembered per board) ---
function readCollapsed() {
	if (!props.storageKey) return null;
	try {
		const raw = window.localStorage.getItem(props.storageKey);
		return raw ? new Set(JSON.parse(raw)) : null;
	} catch {
		return null;
	}
}

const userCollapsed = ref(readCollapsed());

watch(userCollapsed, (value) => {
	if (!props.storageKey || !value) return;
	try {
		window.localStorage.setItem(props.storageKey, JSON.stringify([...value]));
	} catch {
		// storage unavailable - collapsed lists are just not remembered
	}
});

function isCollapsed(status) {
	if (userCollapsed.value) return userCollapsed.value.has(status);
	// Default: extra drop-only lists start collapsed.
	return !listedStatuses.value.includes(status);
}

function toggleCollapse(status) {
	const next = new Set(
		userCollapsed.value ||
			BOARD_STATUSES.filter((value) => !listedStatuses.value.includes(value))
	);
	if (next.has(status)) next.delete(status);
	else next.add(status);
	userCollapsed.value = next;
}

// --- columns ---
const columnStatuses = computed(() => {
	const extra = props.dropStatuses.filter((status) => !listedStatuses.value.includes(status));
	return BOARD_STATUSES.filter(
		(status) => listedStatuses.value.includes(status) || extra.includes(status)
	);
});

// List a task belongs to. The legacy "Overdue" status has no list of its own
// (a missed due date is a flag now), so such tasks stay visible under Open.
function boardStatus(task) {
	const status = pendingStatus.get(task.name) ?? task.status;
	return status === "Overdue" ? "Open" : status;
}

const columns = computed(() =>
	columnStatuses.value.map((status) => {
		const config = getStatusConfig(status);
		return {
			status,
			title: getStatusLabel(status),
			dot: config.dot,
			tasks: props.tasks.filter((task) => boardStatus(task) === status),
		};
	})
);

function cardProps(task) {
	const parent = task.parent_task ? taskByName.value.get(task.parent_task) : null;
	return {
		users: props.users,
		milestone: getTaskMilestone(task, props.milestones),
		parentSubject: task.parent_subject || parent?.subject || "",
		showProject: props.showProject,
		// Counts sent by the server (My Tasks) cover subtasks that are not loaded.
		subtaskStats:
			task.subtask_count != null
				? { total: Number(task.subtask_count) || 0, done: Number(task.subtask_done) || 0 }
				: getSubtaskStats(hierarchy.value, task.name),
	};
}

// --- actions ---
async function move(task, status) {
	if (!status || status === (pendingStatus.get(task.name) ?? task.status)) return;
	pendingStatus.set(task.name, status);
	try {
		await props.moveTask(task, status);
	} catch {
		// the owner reports the error; the card goes back to its list
	} finally {
		pendingStatus.delete(task.name);
	}
}

function create(status) {
	if (!props.createTask) return null;
	return (subject) => props.createTask({ subject, status });
}

function openMenu(task, event) {
	if (menu.value?.task.name === task.name) {
		menu.value = null;
		return;
	}
	const rect = event.currentTarget?.getBoundingClientRect?.();
	const anchor =
		event.type === "contextmenu" || !rect
			? { x: event.clientX, y: event.clientY }
			: { x: rect.left, y: rect.bottom + 4 };
	menu.value = { task, anchor };
}

function closeMenu() {
	menu.value = null;
}

function onMenuStatus(status) {
	if (menu.value) move(menu.value.task, status);
}

function onMenuPriority(priority) {
	const task = menu.value?.task;
	if (task && priority !== task.priority) emit("update", task, { priority });
}

function onToggleBlocked(task) {
	emit("update", task, { is_blocked: task.is_blocked ? 0 : 1 });
}

function onOpenDesk(task) {
	window.open(`/app/task/${encodeURIComponent(task.name)}`, "_blank");
}

defineExpose({ closeMenu });
</script>

<template>
	<div class="task-board h-full overflow-x-auto overflow-y-hidden">
		<div class="flex h-full min-h-[24rem] items-start gap-3 p-4 sm:px-6">
			<TaskBoardColumn
				v-for="column in columns"
				:key="column.status"
				:column="column"
				:collapsed="isCollapsed(column.status)"
				:card-props="cardProps"
				:active-menu-task="menu?.task.name || null"
				:dragging="dragging"
				:create="create(column.status)"
				@toggle-collapse="toggleCollapse(column.status)"
				@drop="(task) => move(task, column.status)"
				@open="(task) => emit('open', task)"
				@menu="openMenu"
				@update="(task, fields) => emit('update', task, fields)"
				@drag-start="dragging = true; closeMenu()"
				@drag-end="dragging = false"
			/>
		</div>

		<TaskQuickMenu
			v-if="menu"
			:task="menu.task"
			:anchor="menu.anchor"
			:statuses="BOARD_STATUSES"
			:priorities="priorities"
			:can-assign-me="canAssignMe"
			:can-log-time="canLogTime"
			:can-delete="canDelete"
			@close="closeMenu"
			@open="(task) => emit('open', task)"
			@status="onMenuStatus"
			@priority="onMenuPriority"
			@assign-me="(task) => emit('assign-me', task)"
			@toggle-blocked="onToggleBlocked"
			@log-time="(task) => emit('log-time', task)"
			@open-desk="onOpenDesk"
			@delete="(task) => emit('delete', task)"
		/>
	</div>
</template>
