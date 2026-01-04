<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import QuickAddTask from './QuickAddTask.vue'
import UserSelect from './UserSelect.vue'
import TimeLogModal from './TimeLogModal.vue?v=20241220-2030'
import {
	X,
	ExternalLink,
	Calendar,
	User,
	Flag,
	Clock,
	CheckCircle2,
	Circle,
	AlertCircle,
	FileText,
	MessageSquare,
	Paperclip,
	ChevronDown,
	Plus,
	Trash2,
	Diamond,
	Folder,
} from 'lucide-vue-next'

const realWindow = typeof globalThis !== 'undefined' ? globalThis.window : undefined
const translate = (text) => {
	return (typeof realWindow !== 'undefined' && typeof realWindow.__ === 'function') ? realWindow.__(text) : text
}

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
})

const emit = defineEmits(['close'])

const store = useTaskStore()

// Local editable state
const editableTask = ref({ ...props.task })
const isSaving = ref(false)
const activeTab = ref('details')
const showTimeLogModal = ref(false)
const timelogsLoading = ref(false)

watch(
	() => props.task,
	(newTask) => {
		editableTask.value = { ...newTask }
	},
	{ deep: true }
)

// Load metadata on mount
onMounted(() => {
	if (store.taskStatuses.length === 0) {
		store.fetchTaskStatuses()
	}
	if (store.taskPriorities.length === 0) {
		store.fetchTaskPriorities()
	}
})

// Status options with icons
const statusIconMap = {
	'Open': Circle,
	'Working': Clock,
	'Pending Review': AlertCircle,
	'Completed': CheckCircle2,
	'Overdue': AlertCircle,
	'Cancelled': Circle,
}

const disabledStatuses = ['Template']

const statusOptions = computed(() => {
	return store.taskStatuses.map(status => ({
		value: status,
		label: status,
		icon: statusIconMap[status] || Circle,
		disabled: disabledStatuses.includes(status),
	}))
})

const priorityOptions = computed(() => {
	return store.taskPriorities.map(priority => ({
		value: priority,
		label: priority
	}))
})

// Milestone handling
async function handleMilestoneChange(event) {
	const newMilestone = event.target.value || null
	try {
		await store.assignTaskToMilestone(props.task.name, newMilestone)
		if (realWindow?.frappe) {
			frappe.show_alert({ 
				message: newMilestone ? translate('Task assigned to milestone') : translate('Task removed from milestone'), 
				indicator: 'green' 
			})
		}
	} catch (error) {
		if (realWindow?.frappe) {
			frappe.show_alert({ message: translate('Failed to update milestone'), indicator: 'red' })
		}
	}
}

// Project change handling
async function handleProjectChange() {
	const newProject = editableTask.value.project
	if (newProject === props.task.project) return
	
	try {
		await store.updateTask(props.task.name, { project: newProject })
		if (realWindow?.frappe) {
			frappe.show_alert({ 
				message: translate('Task project changed'), 
				indicator: 'green' 
			})
		}
	} catch (error) {
		editableTask.value.project = props.task.project
		if (realWindow?.frappe) {
			frappe.show_alert({ message: translate('Failed to change project'), indicator: 'red' })
		}
	}
}

async function saveField(field, value) {
	if (value === props.task[field]) return

	isSaving.value = true
	try {
		await store.updateTask(props.task.name, { [field]: value })
		if (realWindow?.frappe && field === 'exp_end_date') {
			frappe.show_alert({ message: 'Date updated successfully', indicator: 'green' })
		}
	} catch (error) {
		// Revert on error
		editableTask.value[field] = props.task[field]
		if (realWindow?.frappe) {
			frappe.show_alert({ message: 'Failed to update field', indicator: 'red' })
		}
	} finally {
		isSaving.value = false
	}
}

function openInDesk() {
	realWindow?.open(`/app/task/${props.task.name}`, '_blank')
}

async function handleAddAssignee(user) {
	await store.assignTask(props.task.name, user, 'add')
}

async function handleRemoveAssignee(user) {
	await store.assignTask(props.task.name, user, 'remove')
}

onMounted(() => {
	store.fetchUsers()
	store.fetchAllProjects()
	loadTimelogs()
})

const currentTimelogs = computed(() => {
	return store.taskTimelogs[props.task.name] || { timelogs: [], total_hours: 0 }
})

async function loadTimelogs() {
	timelogsLoading.value = true
	try {
		await store.fetchTaskTimelogs(props.task.name)
	} catch (error) {
		console.error('Failed to load timelogs:', error)
	} finally {
		timelogsLoading.value = false
	}
}

async function handleTimeLogSave(timelogData) {
	try {
		await store.createTimelog(timelogData)
		showTimeLogModal.value = false
		if (realWindow?.frappe) {
			frappe.show_alert({ message: 'Time log saved successfully', indicator: 'green' })
		}
	} catch (error) {
		if (realWindow?.frappe) {
			frappe.show_alert({ message: 'Failed to save time log', indicator: 'red' })
		}
	}
}

async function handleDeleteTimelog(timelogName) {
	if (!confirm('Are you sure you want to delete this time log?')) return
	
	try {
		await store.deleteTimelog(timelogName, props.task.name)
		if (realWindow?.frappe) {
			frappe.show_alert({ message: 'Time log deleted', indicator: 'green' })
		}
	} catch (error) {
		if (realWindow?.frappe) {
			frappe.show_alert({ message: 'Failed to delete time log', indicator: 'red' })
		}
	}
}

function formatDate(dateStr) {
	if (!dateStr) return ''
	const date = new Date(dateStr)
	return date.toLocaleString('pl-PL', {
		day: '2-digit',
		month: '2-digit',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
	})
}

async function handleSubtaskCreated() {
	// Refresh tasks and re-select current task to update children
	await store.fetchTasks(props.task.project)
	// Find updated task in store and re-select it
	const updatedTask = store.taskTree.find(t => t.name === props.task.name)
	if (updatedTask) {
		store.selectTask(updatedTask)
	}
}
</script>

<template>
	<aside class="w-96 bg-white border-l border-gray-200 flex flex-col flex-shrink-0 overflow-hidden">
		<!-- Header -->
		<div class="flex items-center justify-between px-4 py-3 border-b border-gray-200">
			<div class="flex items-center gap-2">
				<span class="text-sm font-medium text-gray-500">{{ task.name }}</span>
				<button
					@click="openInDesk"
					class="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
					title="Open in Desk"
				>
					<ExternalLink class="w-4 h-4" />
				</button>
			</div>
			<button
				@click="emit('close')"
				class="p-1 rounded hover:bg-gray-100 text-gray-500"
			>
				<X class="w-5 h-5" />
			</button>
		</div>

		<!-- Content -->
		<div class="flex-1 overflow-y-auto">
			<div class="p-4 space-y-4">
				<!-- Subject -->
				<div>
					<input
						v-model="editableTask.subject"
						type="text"
						class="w-full text-lg font-semibold text-gray-900 border-0 p-0 focus:ring-0 placeholder:text-gray-400"
						placeholder="Task name"
						@blur="saveField('subject', editableTask.subject)"
					/>
				</div>

				<!-- Status -->
				<div>
					<label class="text-sm text-gray-500 mb-2 block">Status</label>
					<div class="grid grid-cols-2 gap-2">
						<button
							v-for="opt in statusOptions"
							:key="opt.value"
							:disabled="opt.disabled"
							@click="!opt.disabled && (editableTask.status = opt.value, saveField('status', opt.value))"
							:class="[
								'flex items-center gap-2 px-3 py-2 border rounded-lg text-sm transition-colors',
								opt.disabled ? 'opacity-50 cursor-not-allowed' : '',
								editableTask.status === opt.value
									? 'border-blue-500 bg-blue-50 text-blue-700'
									: 'border-gray-200 hover:bg-gray-50'
							]"
						>
							<component :is="opt.icon" :class="['w-4 h-4', opt.value === editableTask.status ? 'text-blue-600' : 'text-gray-400']" />
							{{ opt.label }}
						</button>
					</div>
				</div>

				<!-- Priority -->
				<div>
					<label class="text-sm text-gray-500 mb-2 block flex items-center gap-1">
						<Flag class="w-3.5 h-3.5" />
						Priorytet
					</label>
					<div class="grid grid-cols-2 gap-2">
						<button
							v-for="opt in priorityOptions"
							:key="opt.value"
							@click="editableTask.priority = opt.value; saveField('priority', opt.value)"
							:class="[
								'flex items-center gap-2 px-3 py-2 border rounded-lg text-sm transition-colors',
								editableTask.priority === opt.value
									? 'border-blue-500 bg-blue-50 text-blue-700'
									: 'border-gray-200 hover:bg-gray-50'
							]"
						>
							<Flag :class="['w-4 h-4', opt.value === editableTask.priority ? 'text-blue-600' : 'text-gray-400']" />
							{{ opt.label }}
						</button>
					</div>
				</div>

				<!-- Milestone -->
				<div class="flex items-center gap-3">
					<label class="text-sm text-gray-500 w-20 flex items-center gap-1">
						<Diamond class="w-3 h-3" />
						{{ translate('Milestone') }}
					</label>
					<select
						:value="task.milestone || ''"
						@change="handleMilestoneChange"
						class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
					>
								<option value="">{{ translate('No milestone') }}</option>
						<option 
							v-for="milestone in store.milestones" 
							:key="milestone.name" 
							:value="milestone.name"
						>
							{{ milestone.milestone_name }}
						</option>
					</select>
				</div>

				<!-- Project -->
				<div class="flex items-center gap-3">
					<label class="text-sm text-gray-500 w-20 flex items-center gap-1">
						<Folder class="w-3 h-3" />
						{{ translate('Project') }}
					</label>
					<select
						v-model="editableTask.project"
						@change="handleProjectChange"
						class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
					>
						<option 
							v-for="proj in store.allProjects" 
							:key="proj.name" 
							:value="proj.name"
						>
							{{ proj.project_name }}
						</option>
					</select>
				</div>

				<!-- Assignee -->
				<div class="flex items-start gap-3">
					<label class="text-sm text-gray-500 w-20 pt-2">{{ translate('Assigned') }}</label>
					<div class="flex-1">
						<UserSelect
							:model-value="task._assign"
							:placeholder="translate('Assign user...')"
							@add="handleAddAssignee"
							@remove="handleRemoveAssignee"
						/>
					</div>
				</div>

				<!-- Due date -->
				<div class="flex items-center gap-3">
						<label class="text-sm text-gray-500 w-20">{{ translate('Due Date') }}</label>
					<input
						v-model="editableTask.exp_end_date"
						type="date"
						@change="saveField('exp_end_date', editableTask.exp_end_date)"
						class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>

				<!-- Start date -->
				<div class="flex items-center gap-3">
					<label class="text-sm text-gray-500 w-20">{{ translate('Start Date') }}</label>
					<input
						v-model="editableTask.exp_start_date"
						type="date"
						@change="saveField('exp_start_date', editableTask.exp_start_date)"
						class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>

				<!-- Progress -->
				<div class="flex items-center gap-3">
					<label class="text-sm text-gray-500 w-20">{{ translate('Progress') }}</label>
					<div class="flex-1 flex items-center gap-2">
						<input
							v-model.number="editableTask.progress"
							type="range"
							min="0"
							max="100"
							@change="saveField('progress', editableTask.progress)"
							class="flex-1"
						/>
						<span class="text-sm text-gray-600 w-10 text-right">
							{{ editableTask.progress || 0 }}%
						</span>
					</div>
				</div>

				<hr class="border-gray-200" />

				<!-- Description -->
				<div>
					<label class="text-sm font-medium text-gray-700 mb-2 block">{{ translate('Description') }}</label>
					<textarea
						v-model="editableTask.description"
						rows="4"
						class="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
						:placeholder="translate('Add description...')"
						@blur="saveField('description', editableTask.description)"
					></textarea>
				</div>

				<hr class="border-gray-200" />

				<!-- Time Logs -->
				<div>
						<div class="flex items-center justify-between mb-3">
						<div>
							<h3 class="text-sm font-medium text-gray-700">{{ translate('Time Log') }}</h3>
							<p v-if="currentTimelogs.total_hours > 0" class="text-xs text-gray-500 mt-0.5">
								{{ translate('Total') }}: {{ currentTimelogs.total_hours.toFixed(2) }} {{ translate('hrs') }}.
							</p>
						</div>
						<button
							@click="showTimeLogModal = true"
							class="flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
						>
							<Plus class="w-3.5 h-3.5" />
							{{ translate('Add time') }}
						</button>
					</div>

					<div v-if="timelogsLoading" class="text-center py-4">
						<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
					</div>

						<div v-else-if="currentTimelogs.timelogs.length === 0" class="text-sm text-gray-500 text-center py-4">
						{{ translate('No time entries') }}
					</div>

					<div v-else class="space-y-2">
						<div
							v-for="log in currentTimelogs.timelogs"
							:key="log.timelog_name"
							class="bg-gray-50 rounded-md p-3 text-sm"
						>
							<div class="flex items-start justify-between gap-2">
								<div class="flex-1">
									<div class="flex items-center gap-2 mb-1">
										<Clock class="w-3.5 h-3.5 text-blue-600" />
										<span class="font-semibold text-gray-900">{{ log.hours }} hrs</span>
										<span class="text-xs text-gray-500">{{ log.activity_type }}</span>
										<span 
											v-if="log.status" 
											:class="[
												'px-2 py-0.5 rounded-full text-xs font-medium',
												log.status === 'Submitted' ? 'bg-green-100 text-green-800' :
												log.status === 'Billed' ? 'bg-blue-100 text-blue-800' :
												log.status === 'Draft' ? 'bg-gray-100 text-gray-800' :
												'bg-gray-100 text-gray-800'
											]"
										>
											{{ log.status }}
										</span>
									</div>
									<p v-if="log.description" class="text-gray-600 text-xs mb-1">{{ log.description }}</p>
									<div class="flex items-center gap-2 text-xs text-gray-500">
										<span>{{ log.user_full_name }}</span>
										<span>•</span>
										<span>{{ formatDate(log.from_time) }}</span>
									</div>
								</div>
								<button
									@click="handleDeleteTimelog(log.timelog_name)"
									class="p-1 rounded hover:bg-red-100 text-gray-400 hover:text-red-600"
									title="Delete time log"
								>
									<Trash2 class="w-3.5 h-3.5" />
								</button>
							</div>
						</div>
					</div>
				</div>

				<hr class="border-gray-200" />

				<!-- Subtasks -->
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">Podzadania</h3>
					<div v-if="task.children?.length > 0" class="space-y-1 mb-2">
						<div
							v-for="child in task.children"
							:key="child.name"
							class="flex items-center gap-2 text-sm text-gray-600 py-1"
						>
							<component
								:is="child.status === 'Completed' ? CheckCircle2 : Circle"
								:class="[
									'w-4 h-4',
									child.status === 'Completed' ? 'text-green-500' : 'text-gray-400',
								]"
							/>
							<span :class="{ 'line-through text-gray-400': child.status === 'Completed' }">
								{{ child.subject }}
							</span>
						</div>
					</div>
					<QuickAddTask
						:project-id="task.project"
						:parent-task="task.name"
						placeholder="Dodaj podzadanie..."
						@created="handleSubtaskCreated"
					/>
				</div>
			</div>
		</div>

		<!-- Footer -->
		<div class="border-t border-gray-200 px-4 py-3">
			<div class="flex items-center justify-between text-xs text-gray-500">
				<span v-if="task.creation">Utworzono {{ task.creation }}</span>
				<span v-if="isSaving" class="text-blue-600">Zapisywanie...</span>
			</div>
		</div>

		<!-- Time Log Modal -->
		<TimeLogModal
			:task="task"
			:show="showTimeLogModal"
			@close="showTimeLogModal = false"
			@save="handleTimeLogSave"
		/>
	</aside>
</template>
