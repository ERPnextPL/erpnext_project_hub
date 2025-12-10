<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import {
	GripVertical,
	ChevronRight,
	ChevronDown,
	Circle,
	CheckCircle2,
	Clock,
	AlertCircle,
	User,
	Calendar,
	MoreHorizontal,
	Trash2,
	ExternalLink,
	Plus,
	Diamond,
} from 'lucide-vue-next'

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
	level: {
		type: Number,
		default: 0,
	},
})

const emit = defineEmits(['update', 'click', 'add-subtask', 'log-time'])

const store = useTaskStore()

// Inline editing state
const editingField = ref(null)
const editValue = ref('')
const inputRef = ref(null)

// Context menu
const showContextMenu = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })

const hasChildren = computed(() => props.task.children?.length > 0)
const isExpanded = computed(() => store.expandedTasks.has(props.task.name))

const assignedUsers = computed(() => {
	if (!props.task._assign) return []
	try {
		const assigns = JSON.parse(props.task._assign)
		return Array.isArray(assigns) ? assigns : []
	} catch {
		return []
	}
})

const firstAssignee = computed(() => {
	if (assignedUsers.value.length === 0) return null
	const email = assignedUsers.value[0]
	// Extract name from email (before @)
	const name = email.split('@')[0]
	return {
		email,
		displayName: name.charAt(0).toUpperCase() + name.slice(1).replace(/[._]/g, ' ')
	}
})

// Load metadata on mount
onMounted(() => {
	if (store.taskStatuses.length === 0) {
		store.fetchTaskStatuses()
	}
	if (store.taskPriorities.length === 0) {
		store.fetchTaskPriorities()
	}
})

// Status configuration with icons and classes
const statusIconMap = {
	'Open': { icon: Circle, class: 'status-open' },
	'Working': { icon: Clock, class: 'status-working' },
	'Pending Review': { icon: AlertCircle, class: 'status-working' },
	'Completed': { icon: CheckCircle2, class: 'status-completed' },
	'Overdue': { icon: AlertCircle, class: 'status-overdue' },
	'Cancelled': { icon: Circle, class: 'status-cancelled' },
}

const statusLabelMap = {
	'Open': 'Open',
	'Working': 'Working',
	'Pending Review': 'Review',
	'Completed': 'Done',
	'Overdue': 'Overdue',
	'Cancelled': 'Cancelled',
}

const statusConfig = computed(() => {
	const config = {}
	store.taskStatuses.forEach(status => {
		const iconConfig = statusIconMap[status] || { icon: Circle, class: 'status-open' }
		config[status] = {
			icon: iconConfig.icon,
			class: iconConfig.class,
			label: statusLabelMap[status] || status
		}
	})
	return config
})

const priorityClassMap = {
	'Urgent': 'priority-urgent',
	'High': 'priority-high',
	'Medium': 'priority-medium',
	'Low': 'priority-low',
}

const priorityLabelMap = {
	'Urgent': '!!!',
	'High': '!!',
	'Medium': '!',
	'Low': '-',
}

const priorityConfig = computed(() => {
	const config = {}
	store.taskPriorities.forEach(priority => {
		config[priority] = {
			class: priorityClassMap[priority] || 'priority-medium',
			label: priorityLabelMap[priority] || priority.charAt(0)
		}
	})
	return config
})

function toggleExpand() {
	store.toggleExpand(props.task.name)
}

function handleRowClick() {
	emit('click', props.task)
}

function startEditing(field, currentValue) {
	editingField.value = field
	editValue.value = currentValue || ''
	nextTick(() => {
		inputRef.value?.focus()
		inputRef.value?.select()
	})
}

function finishEditing() {
	if (editingField.value && editValue.value !== props.task[editingField.value]) {
		emit('update', props.task.name, { [editingField.value]: editValue.value })
	}
	editingField.value = null
	editValue.value = ''
}

function cancelEditing() {
	editingField.value = null
	editValue.value = ''
}

function handleKeydown(e) {
	if (e.key === 'Enter') {
		finishEditing()
	} else if (e.key === 'Escape') {
		cancelEditing()
	}
}

function cycleStatus() {
	// Use first 4 statuses from store for cycling (typically Open, Working, Pending Review, Completed)
	const cyclableStatuses = store.taskStatuses.slice(0, 4)
	if (cyclableStatuses.length === 0) return
	
	const currentIndex = cyclableStatuses.indexOf(props.task.status)
	const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % cyclableStatuses.length
	const nextStatus = cyclableStatuses[nextIndex]
	emit('update', props.task.name, { status: nextStatus })
}

function showMenu(e) {
	e.preventDefault()
	contextMenuPosition.value = { x: e.clientX, y: e.clientY }
	showContextMenu.value = true

	// Close on click outside
	const closeMenu = () => {
		showContextMenu.value = false
		document.removeEventListener('click', closeMenu)
	}
	setTimeout(() => document.addEventListener('click', closeMenu), 0)
}

async function deleteTask() {
	if (hasChildren.value) {
		if (!confirm('This task has subtasks. Delete all subtasks as well?')) {
			return
		}
	}
	await store.deleteTask(props.task.name)
	showContextMenu.value = false
}

function openInDesk() {
	window.open(`/app/task/${props.task.name}`, '_blank')
}

function addSubtask() {
	emit('add-subtask', props.task.name)
	showContextMenu.value = false
}

function logTime() {
	emit('log-time', props.task)
	showContextMenu.value = false
}
</script>

<template>
	<div
		class="task-row grid grid-cols-12 gap-2 px-4 py-2 items-center cursor-pointer group border-l-2"
		:class="[
			level === 0 ? 'bg-white hover:bg-gray-50 border-transparent' : 
			level === 1 ? 'bg-gray-50/50 hover:bg-gray-100/50 border-blue-200/40' : 
			'bg-gray-100/30 hover:bg-gray-100/60 border-blue-300/30'
		]"
		@click="handleRowClick"
		@contextmenu="showMenu"
	>
		<!-- Task name with indent -->
		<div class="col-span-5 flex items-center gap-1 min-w-0">
			<!-- Drag handle -->
			<div class="drag-handle opacity-0 group-hover:opacity-100 cursor-grab p-1 -ml-2">
				<GripVertical class="w-4 h-4 text-gray-400" />
			</div>

			<!-- Indent spacer with tree lines -->
			<div
				v-for="i in level"
				:key="i"
				class="w-6 flex-shrink-0 relative"
			>
				<!-- Vertical line -->
				<div class="absolute left-3 top-0 bottom-0 w-px bg-gray-200"></div>
			</div>

			<!-- Expand/collapse toggle or connector -->
			<div class="relative flex items-center justify-center" :class="level > 0 ? 'w-6' : 'w-5'">
				<!-- Horizontal connector line for subtasks -->
				<div v-if="level > 0" class="absolute left-0 top-1/2 w-3 h-px bg-gray-200"></div>
				
				<button
					v-if="hasChildren"
					@click.stop="toggleExpand"
					class="p-0.5 rounded hover:bg-gray-200 flex-shrink-0 bg-white relative z-10"
				>
					<ChevronDown v-if="isExpanded" class="w-4 h-4 text-gray-500" />
					<ChevronRight v-else class="w-4 h-4 text-gray-500" />
				</button>
				<div v-else-if="level > 0" class="w-2 h-2 rounded-full bg-gray-300 relative z-10"></div>
			</div>

			<!-- Task subject -->
			<div class="flex-1 min-w-0 flex items-center gap-1">
				<!-- Milestone indicator -->
				<Diamond 
					v-if="task.milestone" 
					class="w-3 h-3 text-blue-500 flex-shrink-0" 
					:title="'Milestone: ' + task.milestone"
				/>
				
				<input
					v-if="editingField === 'subject'"
					ref="inputRef"
					v-model="editValue"
					type="text"
					class="inline-edit-input text-sm flex-1"
					@blur="finishEditing"
					@keydown="handleKeydown"
					@click.stop
				/>
				<span
					v-else
					@dblclick.stop="startEditing('subject', task.subject)"
					class="text-sm text-gray-900 truncate"
					:class="{ 'font-medium': task.is_group }"
				>
					{{ task.subject }}
				</span>
			</div>
		</div>

		<!-- Status -->
		<div class="col-span-2">
			<button
				@click.stop="cycleStatus"
				:class="[
					'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
					statusConfig[task.status]?.class || 'status-open',
				]"
			>
				<component
					:is="statusConfig[task.status]?.icon || Circle"
					class="w-3 h-3"
				/>
				{{ statusConfig[task.status]?.label || task.status }}
			</button>
		</div>

		<!-- Assignee -->
		<div class="col-span-2">
			<div
				v-if="firstAssignee"
				class="flex items-center gap-1 text-sm text-gray-600"
				:title="firstAssignee.email + (assignedUsers.length > 1 ? ' +' + (assignedUsers.length - 1) : '')"
			>
				<User class="w-4 h-4 text-gray-400" />
				<span class="truncate">{{ firstAssignee.displayName }}</span>
				<span v-if="assignedUsers.length > 1" class="text-xs text-gray-400">
					+{{ assignedUsers.length - 1 }}
				</span>
			</div>
			<button
				v-else
				@click.stop
				class="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
			>
				<User class="w-4 h-4" />
			</button>
		</div>

		<!-- Due date -->
		<div class="col-span-2">
			<div
				v-if="editingField === 'exp_end_date'"
				@click.stop
			>
				<input
					ref="inputRef"
					v-model="editValue"
					type="date"
					class="inline-edit-input text-sm"
					@blur="finishEditing"
					@keydown="handleKeydown"
				/>
			</div>
			<div
				v-else-if="task.exp_end_date"
				@dblclick.stop="startEditing('exp_end_date', task.exp_end_date)"
				class="flex items-center gap-1 text-sm text-gray-600"
			>
				<Calendar class="w-4 h-4 text-gray-400" />
				<span>{{ task.exp_end_date }}</span>
			</div>
			<button
				v-else
				@click.stop="startEditing('exp_end_date', '')"
				class="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
			>
				<Calendar class="w-4 h-4" />
			</button>
		</div>

		<!-- Priority -->
		<div class="col-span-1 flex items-center justify-between">
			<span
				v-if="task.priority"
				:class="['text-sm font-bold', priorityConfig[task.priority]?.class]"
			>
				{{ priorityConfig[task.priority]?.label }}
			</span>

			<!-- More menu -->
			<button
				@click.stop="showMenu"
				class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-200"
			>
				<MoreHorizontal class="w-4 h-4 text-gray-500" />
			</button>
		</div>

		<!-- Context menu -->
		<Teleport to="body">
			<div
				v-if="showContextMenu"
				class="fixed bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50 min-w-[160px]"
				:style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }"
			>
				<button
					@click="logTime"
					class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
				>
					<Clock class="w-4 h-4" />
					Log Time
				</button>
				<button
					@click="addSubtask"
					class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
				>
					<Plus class="w-4 h-4" />
					Add subtask
				</button>
				<button
					@click="openInDesk"
					class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
				>
					<ExternalLink class="w-4 h-4" />
					Open in Desk
				</button>
				<hr class="my-1 border-gray-200" />
				<button
					@click="deleteTask"
					class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
				>
					<Trash2 class="w-4 h-4" />
					Delete
				</button>
			</div>
		</Teleport>
	</div>
</template>
