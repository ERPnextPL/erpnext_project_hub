<script setup>
import { ref } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import TaskRow from './TaskRow.vue'
import QuickAddTask from './QuickAddTask.vue'
import TimeLogModal from './TimeLogModal.vue'
import draggable from 'vuedraggable'

const props = defineProps({
	tasks: {
		type: Array,
		required: true,
	},
	projectId: {
		type: String,
		required: true,
	},
})

const store = useTaskStore()
const draggedTask = ref(null)
const addingSubtaskTo = ref(null) // Track which task we're adding a subtask to
const showTimeLogModal = ref(false)
const selectedTaskForTimeLog = ref(null)

function handleDragStart(evt) {
	draggedTask.value = evt.item.__vue__?.task || null
}

function handleDragEnd(evt) {
	if (!draggedTask.value) return

	const newIndex = evt.newIndex
	const oldIndex = evt.oldIndex

	if (newIndex !== oldIndex) {
		// Calculate new parent and idx based on position
		const targetTask = props.tasks[newIndex]
		const newParent = targetTask?.parent_task || null

		store.reorderTask(draggedTask.value.name, newParent, newIndex)
	}

	draggedTask.value = null
}

const highlightedTasks = ref(new Set())

async function handleTaskUpdate(taskName, updates) {
	try {
		await store.updateTask(taskName, updates)
	} catch (error) {
		// Check if this is an incomplete subtasks error
		const errorMsg = error.message || 'Failed to update task'
		const isSubtaskError = errorMsg.includes('subtask') || errorMsg.includes('not completed')
		
		if (window.frappe) {
			// Parse Frappe error message if available
			let displayMsg = errorMsg
			try {
				if (errorMsg.includes('_server_messages')) {
					const parsed = JSON.parse(errorMsg)
					displayMsg = parsed._server_messages || errorMsg
				}
			} catch (e) {
				// Use original message
			}
			
			// Show as info (blue) for subtask errors, red for others
			frappe.show_alert({ 
				message: displayMsg, 
				indicator: isSubtaskError ? 'blue' : 'red' 
			})
			
			// Highlight incomplete subtasks
			if (isSubtaskError) {
				highlightIncompleteSubtasks(taskName)
			}
		}
	}
}

function highlightIncompleteSubtasks(parentTaskName) {
	// Find all subtasks of this parent
	const findSubtasks = (taskName) => {
		const subtasks = []
		store.tasks.forEach(task => {
			if (task.parent_task === taskName) {
				subtasks.push(task)
				// Recursively find children
				subtasks.push(...findSubtasks(task.name))
			}
		})
		return subtasks
	}
	
	const subtasks = findSubtasks(parentTaskName)
	const incompleteSubtasks = subtasks.filter(t => 
		t.status !== 'Completed' && t.status !== 'Cancelled'
	)
	
	// Expand parent to show subtasks
	if (!store.expandedTasks.has(parentTaskName)) {
		store.toggleExpand(parentTaskName)
	}
	
	// Highlight incomplete subtasks
	highlightedTasks.value.clear()
	incompleteSubtasks.forEach(task => {
		highlightedTasks.value.add(task.name)
	})
	
	// Remove highlights after 3 seconds
	setTimeout(() => {
		highlightedTasks.value.clear()
	}, 3000)
}

function handleTaskClick(task) {
	store.selectTask(task)
}

function handleTaskCreated() {
	store.fetchTasks(props.projectId)
	addingSubtaskTo.value = null
}

function handleAddSubtask(parentTaskName) {
	// Expand the parent task if it's not expanded
	if (!store.expandedTasks.has(parentTaskName)) {
		store.toggleExpand(parentTaskName)
	}
	addingSubtaskTo.value = parentTaskName
}

function cancelAddSubtask() {
	addingSubtaskTo.value = null
}

function handleLogTime(task) {
	selectedTaskForTimeLog.value = task
	showTimeLogModal.value = true
}

async function handleTimeLogSave(timelogData) {
	try {
		await store.createTimelog(timelogData)
		showTimeLogModal.value = false
		selectedTaskForTimeLog.value = null
		if (window.frappe) {
			frappe.show_alert({ message: 'Time log saved successfully', indicator: 'green' })
		}
	} catch (error) {
		if (window.frappe) {
			frappe.show_alert({ message: 'Failed to save time log', indicator: 'red' })
		}
	}
}
</script>

<template>
	<div class="task-tree">
		<!-- Table header -->
		<div class="sticky top-0 bg-gray-50 border-b border-gray-200 z-10">
			<div class="grid grid-cols-12 gap-2 px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
				<div class="col-span-5">Task</div>
				<div class="col-span-2">Status</div>
				<div class="col-span-2">Assignee</div>
				<div class="col-span-2">Due Date</div>
				<div class="col-span-1">Priority</div>
			</div>
		</div>

		<!-- Task rows -->
		<div class="divide-y divide-gray-100">
			<draggable
				:list="tasks"
				item-key="name"
				handle=".drag-handle"
				ghost-class="opacity-50"
				@start="handleDragStart"
				@end="handleDragEnd"
			>
				<template #item="{ element: task }">
					<div>
						<TaskRow
							:task="task"
							:level="task.level || 0"
							:highlighted="highlightedTasks.has(task.name)"
							@update="handleTaskUpdate"
							@click="handleTaskClick"
							@add-subtask="handleAddSubtask"
							@log-time="handleLogTime"
						/>
						<!-- Inline subtask input -->
						<div v-if="addingSubtaskTo === task.name" class="bg-blue-50 border-l-2 border-blue-400">
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
		</div>

		<!-- Quick add at bottom -->
		<div class="border-t border-gray-200 bg-white">
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
			@close="showTimeLogModal = false; selectedTaskForTimeLog = null"
			@save="handleTimeLogSave"
		/>
	</div>
</template>
