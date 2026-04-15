<script setup>
import { ref, nextTick, computed, watch } from "vue";
import { useTaskStore } from "../stores/taskStore";
import TaskRow from "./TaskRow.vue";
import QuickAddTask from "./QuickAddTask.vue";
import TimeLogModal from "./TimeLogModal.vue?v=20241220";
import ColumnSettings from "./ColumnSettings.vue";
import draggable from "vuedraggable";
import { ArrowUp, ArrowDown } from "lucide-vue-next";
import { translate } from "../utils/translation";

const props = defineProps({
	tasks: {
		type: Array,
		required: true,
	},
	projectId: {
		type: String,
		required: true,
	},
	showHeader: {
		type: Boolean,
		default: true,
	},
	showQuickAdd: {
		type: Boolean,
		default: true,
	},
	enableReorder: {
		type: Boolean,
		default: true,
	},
});

const store = useTaskStore();
const draggedTask = ref(null);
const addingSubtaskTo = ref(null); // Track which task we're adding a subtask to
const showTimeLogModal = ref(false);
const selectedTaskForTimeLog = ref(null);

// Column visibility settings
const COLUMNS_STORAGE_KEY = 'project-hub-visible-columns';

const COLUMN_WIDTHS = {
	task: "minmax(16rem, 2fr)",
	status: "minmax(8rem, 1fr)",
	assignee: "minmax(10rem, 1fr)",
	due_date: "minmax(9rem, 1fr)",
	expected_time: "minmax(8rem, 1fr)",
	priority: "minmax(6rem, 0.8fr)",
	actions: "3.5rem",
};

const availableColumns = [
	{ id: 'task', label: translate('Task'), sortable: true, required: true },
	{ id: 'status', label: translate('Status'), sortable: true },
	{ id: 'assignee', label: translate('Assignee'), sortable: true },
	{ id: 'due_date', label: translate('Due Date'), sortable: true },
	{ id: 'expected_time', label: translate('Expected Time'), sortable: true },
	{ id: 'priority', label: translate('Priority'), sortable: true },
];

const visibleColumns = ref([]);

// Load visible columns from localStorage or use defaults
function loadVisibleColumns() {
	try {
		const saved = localStorage.getItem(COLUMNS_STORAGE_KEY);
		if (saved) {
			const parsed = JSON.parse(saved);
			// Ensure 'task' column is always visible
			if (!parsed.includes('task')) {
				parsed.unshift('task');
			}
			visibleColumns.value = parsed;
		} else {
			// Default visible columns
			visibleColumns.value = ['task', 'status', 'assignee', 'due_date', 'priority'];
		}
	} catch (error) {
		console.error('Failed to load visible columns:', error);
		visibleColumns.value = ['task', 'status', 'assignee', 'due_date', 'priority'];
	}
}

// Save visible columns to localStorage
function saveVisibleColumns(columns) {
	try {
		localStorage.setItem(COLUMNS_STORAGE_KEY, JSON.stringify(columns));
		visibleColumns.value = columns;
	} catch (error) {
		console.error('Failed to save visible columns:', error);
	}
}

// Initialize on mount
loadVisibleColumns();

// Watch for changes and save
watch(visibleColumns, (newColumns) => {
	saveVisibleColumns(newColumns);
});

// Compute column span for grid
const gridCols = computed(() => {
	return visibleColumns.value.length + 1; // +1 for actions column
});

// Get visible column config
const visibleColumnConfigs = computed(() => {
	// Keep header order identical to row cell order (visibleColumns).
	const byId = new Map(availableColumns.map((col) => [col.id, col]));
	return visibleColumns.value
		.map((id) => byId.get(id))
		.filter(Boolean);
});

// Shared grid template so header and rows stay aligned
const gridTemplateColumns = computed(() => {
	const cols = visibleColumns.value.map((id) => COLUMN_WIDTHS[id] || "1fr");
	cols.push(COLUMN_WIDTHS.actions);
	return cols.join(" ");
});

function focusBottomQuickAdd() {
	nextTick(() => {
		const el = document.querySelector(".task-tree-bottom-quickadd .quick-add-input");
		el?.focus();
	});
}

function handleDragStart(evt) {
	if (!props.enableReorder) return;
	draggedTask.value = evt.item.__vue__?.task || null;
}

function handleDragEnd(evt) {
	if (!props.enableReorder) return;
	if (!draggedTask.value) return;

	const newIndex = evt.newIndex;
	const oldIndex = evt.oldIndex;

	if (newIndex !== oldIndex) {
		// Calculate new parent and idx based on position
		const targetTask = props.tasks[newIndex];
		const newParent = targetTask?.parent_task || null;

		store.reorderTask(draggedTask.value.name, newParent, newIndex);
	}

	draggedTask.value = null;
}

const highlightedTasks = ref(new Set());

async function handleTaskUpdate(taskName, updates) {
	try {
		await store.updateTask(taskName, updates);
	} catch (error) {
		// Check if this is an incomplete subtasks error
		const errorMsg = error.message || translate("Failed to update task");
		const isSubtaskError = errorMsg.includes("subtask") || errorMsg.includes("not completed");

		if (window.frappe) {
			// Parse Frappe error message if available
			let displayMsg = errorMsg;
			try {
				if (errorMsg.includes("_server_messages")) {
					const parsed = JSON.parse(errorMsg);
					displayMsg = parsed._server_messages || errorMsg;
				}
			} catch (e) {
				// Use original message
			}

			// Show as info (blue) for subtask errors, red for others
			frappe.show_alert({
				message: displayMsg,
				indicator: isSubtaskError ? "blue" : "red",
			});

			// Highlight incomplete subtasks
			if (isSubtaskError) {
				highlightIncompleteSubtasks(taskName);
			}
		}
	}
}

function highlightIncompleteSubtasks(parentTaskName) {
	// Find all subtasks of this parent
	const findSubtasks = (taskName) => {
		const subtasks = [];
		store.tasks.forEach((task) => {
			if (task.parent_task === taskName) {
				subtasks.push(task);
				// Recursively find children
				subtasks.push(...findSubtasks(task.name));
			}
		});
		return subtasks;
	};

	const subtasks = findSubtasks(parentTaskName);
	const incompleteSubtasks = subtasks.filter(
		(t) => t.status !== "Completed" && t.status !== "Cancelled"
	);

	// Expand parent to show subtasks
	if (!store.expandedTasks.has(parentTaskName)) {
		store.toggleExpand(parentTaskName);
	}

	// Highlight incomplete subtasks
	highlightedTasks.value.clear();
	incompleteSubtasks.forEach((task) => {
		highlightedTasks.value.add(task.name);
	});

	// Remove highlights after 3 seconds
	setTimeout(() => {
		highlightedTasks.value.clear();
	}, 3000);
}

function handleTaskClick(task) {
	store.selectTask(task);
}

function handleTaskCreated() {
	store.fetchTasks(props.projectId);
	addingSubtaskTo.value = null;
}

function handleAddSubtask(parentTaskName) {
	const parent = store.tasks.find((t) => t.name === parentTaskName);
	if (parent && (parent.status === "Completed" || parent.status === "Cancelled")) {
		return;
	}
	// Expand the parent task if it's not expanded
	if (!store.expandedTasks.has(parentTaskName)) {
		store.toggleExpand(parentTaskName);
	}
	addingSubtaskTo.value = parentTaskName;
}

function handleAddTask() {
	addingSubtaskTo.value = null;
	focusBottomQuickAdd();
}

function cancelAddSubtask() {
	addingSubtaskTo.value = null;
}

function handleLogTime(task) {
	selectedTaskForTimeLog.value = task;
	showTimeLogModal.value = true;
}

async function handleTimeLogSave(timelogData) {
	try {
		await store.createTimelog(timelogData);
		showTimeLogModal.value = false;
		selectedTaskForTimeLog.value = null;
		if (window.frappe) {
			frappe.show_alert({ message: translate("Time log saved successfully"), indicator: "green" });
		}
	} catch (error) {
		if (window.frappe) {
			frappe.show_alert({ message: translate("Failed to save time log"), indicator: "red" });
		}
	}
}

function getSortIcon(column) {
	if (store.sortBy !== column) return null;
	return store.sortOrder === "asc" ? ArrowUp : ArrowDown;
}

function handleSort(column) {
	store.setSorting(column);
}

// Sortowane zadania
const sortedTasks = computed(() => {
	if (!store.sortBy) return props.tasks;

	const tasksCopy = [...props.tasks];
	const multiplier = store.sortOrder === "asc" ? 1 : -1;

	tasksCopy.sort((a, b) => {
		let aVal, bVal;

		switch (store.sortBy) {
			case "task":
				aVal = (a.subject || "").toLowerCase();
				bVal = (b.subject || "").toLowerCase();
				break;
			case "status":
				aVal = a.status || "";
				bVal = b.status || "";
				break;
			case "assignee":
				aVal = (a._assign || "").toLowerCase();
				bVal = (b._assign || "").toLowerCase();
				break;
			case "due_date":
				aVal = a.exp_end_date || "9999-12-31";
				bVal = b.exp_end_date || "9999-12-31";
				break;
			case "expected_time":
				aVal = a.expected_time || 0;
				bVal = b.expected_time || 0;
				break;
			case "priority":
				const priorityOrder = { "Urgent": 1, "High": 2, "Medium": 3, "Low": 4 };
				aVal = priorityOrder[a.priority] || 5;
				bVal = priorityOrder[b.priority] || 5;
				break;
			default:
				return 0;
		}

		if (aVal < bVal) return -1 * multiplier;
		if (aVal > bVal) return 1 * multiplier;
		return 0;
	});

	return tasksCopy;
});
</script>

<template>
	<div class="task-tree">
		<!-- Table header -->
		<div
			v-if="showHeader"
			class="sticky top-0 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 z-10"
		>
			<div
				class="grid gap-2 px-4 py-2 items-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
				:style="{ gridTemplateColumns: gridTemplateColumns }"
			>
				<button
					v-for="column in visibleColumnConfigs"
					:key="column.id"
					@click="column.sortable ? handleSort(column.id) : null"
					class="text-left hover:text-gray-700 dark:hover:text-gray-300 transition-colors flex items-center gap-1"
					:class="column.id === 'task' ? 'min-w-0' : ''"
					:style="column.id === 'task' ? { width: '100%' } : {}"
				>
					{{ column.label }}
					<component v-if="getSortIcon(column.id)" :is="getSortIcon(column.id)" class="w-3 h-3" />
				</button>
				<div class="flex justify-end">
					<ColumnSettings
						:available-columns="availableColumns"
						:visible-columns="visibleColumns"
						@update:visibleColumns="saveVisibleColumns"
					/>
				</div>
			</div>
		</div>

		<!-- Task rows -->
		<div class="divide-y divide-gray-100 dark:divide-gray-800">
			<draggable
				v-if="enableReorder"
				:list="sortedTasks"
				item-key="name"
				handle=".drag-handle"
				ghost-class="opacity-50"
				:disabled="!!store.sortBy"
				@start="handleDragStart"
				@end="handleDragEnd"
			>
				<template #item="{ element: task }">
					<div>
						<TaskRow
							:task="task"
							:level="task.level || 0"
							:highlighted="highlightedTasks.has(task.name)"
							:visible-columns="visibleColumns"
							:grid-template="gridTemplateColumns"
							@update="handleTaskUpdate"
							@click="handleTaskClick"
							@add-subtask="handleAddSubtask"
							@log-time="handleLogTime"
							@add-task="handleAddTask"
						/>
						<!-- Inline subtask input -->
						<div
							v-if="addingSubtaskTo === task.name"
							class="bg-blue-50 dark:bg-blue-900/30 border-l-2 border-blue-400 dark:border-blue-500/60"
						>
							<QuickAddTask
								:project-id="projectId"
								:parent-task="task.name"
								:placeholder="'Add subtask to ' + task.subject + '...'"
								:auto-focus="true"
								@created="handleTaskCreated"
								@cancel="cancelAddSubtask"
							/>
						</div>
					</div>
				</template>
				</draggable>
			<div v-else>
				<div v-for="task in sortedTasks" :key="task.name">
					<TaskRow
						:task="task"
						:level="task.level || 0"
						:highlighted="highlightedTasks.has(task.name)"
						:visible-columns="visibleColumns"
						:grid-template="gridTemplateColumns"
						@update="handleTaskUpdate"
						@click="handleTaskClick"
						@add-subtask="handleAddSubtask"
						@log-time="handleLogTime"
						@add-task="handleAddTask"
					/>
					<div
						v-if="addingSubtaskTo === task.name"
						class="bg-blue-50 dark:bg-blue-900/30 border-l-2 border-blue-400 dark:border-blue-500/60"
					>
						<QuickAddTask
							:project-id="projectId"
							:parent-task="task.name"
							:placeholder="'Add subtask to ' + task.subject + '...'"
							:auto-focus="true"
							@created="handleTaskCreated"
							@cancel="cancelAddSubtask"
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- Quick add at bottom -->
		<div
			v-if="showQuickAdd"
			class="task-tree-bottom-quickadd border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
		>
			<QuickAddTask
				:project-id="projectId"
				:parent-task="null"
				placeholder="Add a task..."
				@created="handleTaskCreated"
			/>
		</div>

		<!-- Time Log Modal -->
		<TimeLogModal
			v-if="selectedTaskForTimeLog"
			:task="selectedTaskForTimeLog"
			:show="showTimeLogModal"
			@close="
				showTimeLogModal = false;
				selectedTaskForTimeLog = null;
			"
			@save="handleTimeLogSave"
		/>
	</div>
</template>
