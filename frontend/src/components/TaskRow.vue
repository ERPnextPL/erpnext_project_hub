<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
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
	highlighted: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['update', 'click', 'add-subtask', 'log-time', 'add-task'])

const store = useTaskStore()

// Inline editing state
const editingField = ref(null)
const editValue = ref('')
const inputRef = ref(null)

// Tooltip hint for milestone drag
const showMilestoneHint = ref(false)
const milestoneHintTimeout = ref(null)

// Context menu
const showContextMenu = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })

// User assignment dropdown
const showUserDropdown = ref(false)
const userDropdownPosition = ref({ x: 0, y: 0 })

const hasChildren = computed(() => {
	// Check if any task has this task as parent
	return store.tasks.some(t => t.parent_task === props.task.name)
})
const isExpanded = computed(() => store.expandedTasks.has(props.task.name))

const canAddSubtask = computed(() => {
	return props.task.status !== 'Completed' && props.task.status !== 'Cancelled'
})

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

const milestoneColor = computed(() => {
	if (!props.task.milestone) return null
	const milestone = store.milestones.find(m => m.name === props.task.milestone)
	return milestone?.color || '#3b82f6' // Default blue if no color set
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

async function cycleStatus() {
	// Filter out non-workflow statuses like Overdue (Cancelled is included but has special handling)
	const excludedStatuses = ['Overdue', 'Template']
	const cyclableStatuses = store.taskStatuses.filter(s => !excludedStatuses.includes(s))
	
	if (cyclableStatuses.length === 0) return
	
	if (props.task.status === 'Completed') {
		const targetStatus = cyclableStatuses.includes('Working') ? 'Working' : cyclableStatuses[0]
		emit('update', props.task.name, { status: targetStatus })
		return
	}
	
	const currentIndex = cyclableStatuses.indexOf(props.task.status)
	
	// If current status is not in cycle (e.g. it was Overdue), reset to first status (usually Open)
	if (currentIndex === -1) {
		emit('update', props.task.name, { status: cyclableStatuses[0] })
		return
	}

	const nextIndex = (currentIndex + 1) % cyclableStatuses.length
	const nextStatus = cyclableStatuses[nextIndex]
	
	// Special handling for Cancelled status
	if (nextStatus === 'Cancelled') {
		// Check if task has any subtasks
		const subtasks = store.tasks.filter(t => t.parent_task === props.task.name)
		if (subtasks.length > 0) {
			await handleCancelWithSubtasks()
			return
		}
	}
	
	emit('update', props.task.name, { status: nextStatus })
}

async function handleCancelWithSubtasks() {
	// Count all subtasks recursively
	const countSubtasks = (taskName) => {
		let count = 0
		store.tasks.forEach(task => {
			if (task.parent_task === taskName) {
				count++
				count += countSubtasks(task.name)
			}
		})
		return count
	}
	
	const subtaskCount = countSubtasks(props.task.name)
	
	// Ask for confirmation
	const confirmed = confirm(
		`To zadanie ma ${subtaskCount} podzadań.\n\n` +
		`Anulowanie tego zadania spowoduje również anulowanie wszystkich podzadań.\n\n` +
		`Czy chcesz kontynuować?`
	)
	
	if (!confirmed) return
	
	// Cancel the main task
	emit('update', props.task.name, { status: 'Cancelled' })
	
	// Cancel all subtasks recursively
	const cancelSubtasks = async (taskName) => {
		const subtasks = store.tasks.filter(task => task.parent_task === taskName)
		for (const subtask of subtasks) {
			await store.updateTask(subtask.name, { status: 'Cancelled' })
			// Recursively cancel children
			await cancelSubtasks(subtask.name)
		}
	}
	
	await cancelSubtasks(props.task.name)
	
	// Show success message
	if (window.frappe) {
		frappe.show_alert({ 
			message: `Zadanie i ${subtaskCount} podzadań zostało anulowane`, 
			indicator: 'orange' 
		})
	}
}

function showUserAssignDropdown(e) {
	e.preventDefault()
	e.stopPropagation()
	userDropdownPosition.value = { x: e.clientX, y: e.clientY }
	showUserDropdown.value = true

	// Close on click outside
	const closeDropdown = () => {
		showUserDropdown.value = false
		document.removeEventListener('click', closeDropdown)
	}
	setTimeout(() => document.addEventListener('click', closeDropdown), 0)
}

async function assignCurrentUser() {
	const currentUser = window.frappe?.session?.user
	if (currentUser) {
		await store.assignTask(props.task.name, currentUser, 'add')
		showUserDropdown.value = false
		if (window.frappe) {
			frappe.show_alert({ message: 'Użytkownik przypisany', indicator: 'green' })
		}
	}
}

async function assignUser(user) {
	await store.assignTask(props.task.name, user, 'add')
	showUserDropdown.value = false
	if (window.frappe) {
		frappe.show_alert({ message: 'Użytkownik przypisany', indicator: 'green' })
	}
}

function showMenu(e) {
	if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(hover: none)').matches) {
		return
	}
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
		if (!confirm('To zadanie ma podzadania. Usunąć również wszystkie podzadania?')) {
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
	if (!canAddSubtask.value) return
	emit('add-subtask', props.task.name)
	showContextMenu.value = false
}

function addTask() {
	emit('add-task', props.task.project)
	showContextMenu.value = false
}

function logTime() {
	emit('log-time', props.task)
	showContextMenu.value = false
}

// Drag handlers for milestone assignment
function handleDragStart(event) {
	event.dataTransfer.effectAllowed = 'move'
	event.dataTransfer.setData('text/plain', props.task.name)
	showMilestoneHint.value = false
	if (milestoneHintTimeout.value) {
		clearTimeout(milestoneHintTimeout.value)
	}
}

function handleDragEnd(event) {
	// Cleanup if needed
}

function showHint() {
	// Show hint for 3 seconds when hovering over milestone drag handle
	showMilestoneHint.value = true
	if (milestoneHintTimeout.value) {
		clearTimeout(milestoneHintTimeout.value)
	}
	milestoneHintTimeout.value = setTimeout(() => {
		showMilestoneHint.value = false
	}, 3000)
}

function hideHint() {
	if (milestoneHintTimeout.value) {
		clearTimeout(milestoneHintTimeout.value)
	}
	showMilestoneHint.value = false
}

// Close context menu when clicking outside
function handleGlobalClick(event) {
	if (showContextMenu.value && !event.target.closest('.context-menu-wrapper')) {
		showContextMenu.value = false
	}
}

onMounted(() => {
	document.addEventListener('click', handleGlobalClick)
})

onUnmounted(() => {
	document.removeEventListener('click', handleGlobalClick)
})
</script>

<template>
	<div
		class="task-row grid grid-cols-12 gap-2 px-4 py-2 items-center cursor-pointer group border-l-2 transition-all context-menu-wrapper"
		:class="[
			highlighted ? 'highlight-pulse' : '',
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
			<div 
				class="drag-handle opacity-0 group-hover:opacity-100 cursor-grab p-1 -ml-2"
				title="Przeciągnij, aby zmienić kolejność"
			>
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
			<div class="flex-1 min-w-0 flex items-center gap-1 relative">
				<!-- Milestone drag handle (available for all tasks) -->
				<div
					draggable="true"
					@dragstart="handleDragStart"
					@dragend="handleDragEnd"
					@mouseenter="showHint"
					@mouseleave="hideHint"
					@click.stop
					class="milestone-drag-handle opacity-0 group-hover:opacity-100 cursor-grab p-0.5 -ml-1 relative"
					:title="task.milestone ? '◆ Przeciągnij, aby zmienić kamień milowy' : '◆ Przeciągnij, aby przypisać do kamienia milowego'"
				>
					<Diamond 
						:class="[
							'w-3 h-3 flex-shrink-0',
							!task.milestone && 'text-gray-400'
						]"
						:style="task.milestone && milestoneColor ? { color: milestoneColor } : {}"
					/>
					
					<!-- Hint tooltip -->
					<Transition name="fade">
						<div
							v-if="showMilestoneHint"
							class="absolute left-full ml-2 top-1/2 -translate-y-1/2 z-50 whitespace-nowrap"
						>
							<div class="bg-blue-600 text-white text-xs px-3 py-1.5 rounded-lg shadow-lg flex items-center gap-2">
								<Diamond class="w-3 h-3" />
								<span>Przeciągnij, aby przypisać do kamienia milowego</span>
							</div>
						</div>
					</Transition>
				</div>
				
				<!-- Milestone indicator (always visible if assigned) -->
				<Diamond 
					v-if="task.milestone" 
					class="w-3 h-3 flex-shrink-0" 
					:style="{ color: milestoneColor }"
					:title="'Kamień milowy: ' + task.milestone"
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
				@click.stop="showUserAssignDropdown"
				class="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
				title="Kliknij, aby przypisać użytkownika"
			>
				<User class="w-4 h-4" />
			</button>
			
			<!-- User assignment dropdown -->
			<Teleport to="body">
				<div
					v-if="showUserDropdown"
					class="fixed z-50 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-48"
					:style="{ left: userDropdownPosition.x + 'px', top: userDropdownPosition.y + 'px' }"
				>
					<div class="px-3 py-2 text-xs font-medium text-gray-500 border-b border-gray-100">Przypisz użytkownika</div>
					<button
						@click="assignCurrentUser"
						class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700"
					>
						<User class="w-4 h-4" />
						Przypisz do mnie
					</button>
					<div v-if="store.availableUsers && store.availableUsers.length > 0" class="border-t border-gray-100 mt-1 pt-1">
						<button
							v-for="user in store.availableUsers.slice(0, 5)"
							:key="user.name"
							@click="assignUser(user.name)"
							class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
						>
							<User class="w-4 h-4 text-gray-400" />
							{{ user.full_name || user.name.split('@')[0] }}
						</button>
					</div>
					<div class="border-t border-gray-100 mt-1 pt-1">
						<button
							@click="handleRowClick(); showUserDropdown = false"
							class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 hover:bg-gray-50"
						>
							Więcej opcji...
						</button>
					</div>
				</div>
			</Teleport>
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
					Dodaj czas
				</button>
				<button
					v-if="canAddSubtask"
					@click="addSubtask"
					class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
				>
					<Plus class="w-4 h-4" />
					Dodaj podzadanie
				</button>
				<button
					@click="openInDesk"
					class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
				>
					<ExternalLink class="w-4 h-4" />
					Otwórz w Desk
				</button>
				<hr class="my-1 border-gray-200" />
				<button
					@click="deleteTask"
					class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
				>
					<Trash2 class="w-4 h-4" />
					Usuń
				</button>
			</div>
		</Teleport>
	</div>
</template>

<style scoped>
@keyframes pulse-highlight {
	0%, 100% {
		background-color: rgb(239 246 255); /* blue-50 */
		border-left-color: rgb(59 130 246); /* blue-500 */
	}
	50% {
		background-color: rgb(219 234 254); /* blue-100 */
		border-left-color: rgb(37 99 235); /* blue-600 */
	}
}

.highlight-pulse {
	animation: pulse-highlight 1s ease-in-out 3;
	border-left-width: 4px !important;
}

.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
