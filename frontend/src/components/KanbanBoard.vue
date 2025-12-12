<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import {
	Circle,
	CheckCircle2,
	Clock,
	AlertCircle,
	User,
	Calendar,
	GripVertical,
	Plus,
	ListTodo,
	Flag,
} from 'lucide-vue-next'

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

const emit = defineEmits(['task-click', 'task-update'])

const store = useTaskStore()

// Status configuration
const statusConfig = {
	'Open': { icon: Circle, color: 'bg-blue-500', bgColor: 'bg-blue-50', textColor: 'text-blue-700' },
	'Working': { icon: Clock, color: 'bg-amber-500', bgColor: 'bg-amber-50', textColor: 'text-amber-700' },
	'Pending Review': { icon: AlertCircle, color: 'bg-purple-500', bgColor: 'bg-purple-50', textColor: 'text-purple-700' },
	'Completed': { icon: CheckCircle2, color: 'bg-green-500', bgColor: 'bg-green-50', textColor: 'text-green-700' },
	'Cancelled': { icon: Circle, color: 'bg-gray-400', bgColor: 'bg-gray-50', textColor: 'text-gray-500' },
}

const statusLabels = {
	'Open': 'Open',
	'Working': 'In Progress',
	'Pending Review': 'Review',
	'Completed': 'Completed',
	'Cancelled': 'Cancelled',
}

// Get columns based on available statuses
const columns = computed(() => {
	const statuses = ['Open', 'Working', 'Pending Review', 'Completed', 'Cancelled']
	return statuses.map(status => ({
		id: status,
		title: statusLabels[status] || status,
		...statusConfig[status],
		tasks: props.tasks.filter(t => t.status === status)
	}))
})

// Drag and drop state
const draggedTask = ref(null)
const dragOverColumn = ref(null)

function onDragStart(e, task) {
	draggedTask.value = task
	e.dataTransfer.effectAllowed = 'move'
	e.dataTransfer.setData('text/plain', task.name)
}

function onDragEnd() {
	draggedTask.value = null
	dragOverColumn.value = null
}

function onDragOver(e, columnId) {
	e.preventDefault()
	e.dataTransfer.dropEffect = 'move'
	dragOverColumn.value = columnId
}

function onDragLeave() {
	dragOverColumn.value = null
}

async function onDrop(e, columnId) {
	e.preventDefault()
	dragOverColumn.value = null
	
	if (draggedTask.value && draggedTask.value.status !== columnId) {
		await store.updateTask(draggedTask.value.name, { status: columnId })
		if (window.frappe) {
			frappe.show_alert({ 
				message: `Task moved to ${statusLabels[columnId] || columnId}`, 
				indicator: 'green' 
			})
		}
	}
	draggedTask.value = null
}

function handleTaskClick(task) {
	emit('task-click', task)
}

function getAssignee(task) {
	if (!task._assign) return null
	try {
		const assigns = JSON.parse(task._assign)
		if (Array.isArray(assigns) && assigns.length > 0) {
			const email = assigns[0]
			const name = email.split('@')[0]
			return {
				email,
				displayName: name.charAt(0).toUpperCase() + name.slice(1).replace(/[._]/g, ' '),
				initials: name.charAt(0).toUpperCase()
			}
		}
	} catch {
		return null
	}
	return null
}

function formatDate(dateStr) {
	if (!dateStr) return null
	const date = new Date(dateStr)
	const today = new Date()
	const diffDays = Math.ceil((date - today) / (1000 * 60 * 60 * 24))
	
	if (diffDays < 0) return { text: 'Overdue', class: 'text-red-600 bg-red-50' }
	if (diffDays === 0) return { text: 'Today', class: 'text-amber-600 bg-amber-50' }
	if (diffDays === 1) return { text: 'Tomorrow', class: 'text-blue-600 bg-blue-50' }
	
	return { 
		text: date.toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit' }), 
		class: 'text-gray-600 bg-gray-50' 
	}
}

const priorityColors = {
	'Urgent': 'border-l-red-500',
	'High': 'border-l-orange-500',
	'Medium': 'border-l-yellow-500',
	'Low': 'border-l-gray-300',
}

const priorityBadgeColors = {
	'Urgent': 'bg-red-100 text-red-700',
	'High': 'bg-orange-100 text-orange-700',
	'Medium': 'bg-yellow-100 text-yellow-700',
	'Low': 'bg-gray-100 text-gray-600',
}

// Count subtasks for a task
function getSubtaskCount(task) {
	if (!props.tasks) return 0
	return props.tasks.filter(t => t.parent_task === task.name).length
}
</script>

<template>
	<div class="h-full overflow-x-auto p-4">
		<div class="flex gap-4 h-full min-w-max">
			<!-- Kanban columns -->
			<div
				v-for="column in columns"
				:key="column.id"
				class="flex flex-col w-72 flex-shrink-0"
				@dragover="onDragOver($event, column.id)"
				@dragleave="onDragLeave"
				@drop="onDrop($event, column.id)"
			>
				<!-- Column header -->
				<div 
					class="flex items-center gap-2 px-3 py-2 rounded-t-lg"
					:class="column.bgColor"
				>
					<div 
						class="w-2 h-2 rounded-full"
						:class="column.color"
					></div>
					<h3 class="text-sm font-semibold" :class="column.textColor">
						{{ column.title }}
					</h3>
					<span class="text-xs px-1.5 py-0.5 rounded-full bg-white/50" :class="column.textColor">
						{{ column.tasks.length }}
					</span>
				</div>

				<!-- Column content -->
				<div 
					class="flex-1 bg-gray-50 rounded-b-lg p-2 space-y-2 overflow-y-auto min-h-96 transition-colors"
					:class="dragOverColumn === column.id ? 'bg-blue-50 ring-2 ring-blue-300 ring-inset' : ''"
				>
					<!-- Task cards -->
					<div
						v-for="task in column.tasks"
						:key="task.name"
						draggable="true"
						@dragstart="onDragStart($event, task)"
						@dragend="onDragEnd"
						@click="handleTaskClick(task)"
						class="bg-white rounded-lg shadow-sm border border-gray-200 p-3 cursor-pointer hover:shadow-md transition-shadow group border-l-4"
						:class="[
							priorityColors[task.priority] || 'border-l-gray-200',
							draggedTask?.name === task.name ? 'opacity-50' : ''
						]"
					>
						<!-- Task subject -->
						<div class="flex items-start gap-2">
							<GripVertical class="w-4 h-4 text-gray-300 opacity-0 group-hover:opacity-100 flex-shrink-0 mt-0.5 cursor-grab" />
							<p class="text-sm font-medium text-gray-900 flex-1 line-clamp-2">
								{{ task.subject }}
							</p>
						</div>

						<!-- Task metadata row 1: Priority badge -->
						<div v-if="task.priority" class="mt-2">
							<span 
								class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
								:class="priorityBadgeColors[task.priority] || 'bg-gray-100 text-gray-600'"
							>
								<Flag class="w-3 h-3" />
								{{ task.priority }}
							</span>
						</div>

						<!-- Task metadata row 2: Due date, subtasks, assignee -->
						<div class="flex items-center justify-between mt-2">
							<div class="flex items-center gap-2 flex-wrap">
								<!-- Due date -->
								<div 
									v-if="task.exp_end_date && formatDate(task.exp_end_date)"
									class="flex items-center gap-1 text-xs px-1.5 py-0.5 rounded"
									:class="formatDate(task.exp_end_date).class"
								>
									<Calendar class="w-3 h-3" />
									{{ formatDate(task.exp_end_date).text }}
								</div>
								
								<!-- Subtasks count -->
								<div 
									v-if="getSubtaskCount(task) > 0"
									class="flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-purple-50 text-purple-600"
								>
									<ListTodo class="w-3 h-3" />
									{{ getSubtaskCount(task) }}
								</div>
							</div>

							<!-- Assignee avatar -->
							<div 
								v-if="getAssignee(task)"
								class="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-xs font-medium text-blue-700"
								:title="getAssignee(task).email"
							>
								{{ getAssignee(task).initials }}
							</div>
							<div 
								v-else
								class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center"
							>
								<User class="w-3 h-3 text-gray-400" />
							</div>
						</div>
					</div>

					<!-- Empty state -->
					<div 
						v-if="column.tasks.length === 0"
						class="flex flex-col items-center justify-center py-8 text-gray-400"
					>
						<component :is="column.icon" class="w-8 h-8 mb-2 opacity-50" />
						<p class="text-sm">No tasks</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.line-clamp-2 {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}
</style>
