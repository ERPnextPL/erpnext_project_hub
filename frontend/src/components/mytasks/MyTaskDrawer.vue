<script setup>
import { ref, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useMyTasksStore } from '../../stores/myTasksStore'
import dayjs from 'dayjs'
import {
	X,
	Save,
	Loader2,
	Folder,
	Calendar,
	Flag,
	Circle,
	Clock,
	CheckCircle2,
	AlertCircle,
	FileText,
	Trash2,
	Plus,
} from 'lucide-vue-next'

const props = defineProps({
	isOpen: {
		type: Boolean,
		default: false,
	},
	task: {
		type: Object,
		default: null,
	},
	isNew: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['close', 'created'])

const store = useMyTasksStore()

// Form state
const form = ref({
	subject: '',
	project: '',
	status: 'Open',
	priority: 'Medium',
	exp_end_date: '',
	description: '',
})

const saving = ref(false)
const errors = ref({})
const showTimeLogForm = ref(false)
const timelogsLoading = ref(false)
const timelogForm = ref({
	hours: '',
	activity_type: '',
	description: '',
	from_time: '',
})

const showSubtaskForm = ref(false)
const subtaskSubject = ref('')
const newTaskParentTask = ref(null)

const initialForm = ref(null)

function normalizeFormForCompare(v) {
	return {
		subject: (v?.subject || '').trim(),
		project: v?.project || '',
		status: v?.status || 'Open',
		priority: v?.priority || 'Medium',
		exp_end_date: v?.exp_end_date || '',
		description: (v?.description || '').trim(),
	}
}

function setInitialFormSnapshot() {
	initialForm.value = normalizeFormForCompare(form.value)
}

const isDirty = computed(() => {
	if (!initialForm.value) return false
	const current = normalizeFormForCompare(form.value)
	return JSON.stringify(current) !== JSON.stringify(initialForm.value)
})

// Status and priority options
const statusOptions = [
	{ value: 'Open', label: window.__('Open'), icon: Circle, class: 'text-blue-600' },
	{ value: 'Working', label: window.__('Working'), icon: Clock, class: 'text-amber-600' },
	{ value: 'Pending Review', label: window.__('Pending Review'), icon: AlertCircle, class: 'text-purple-600' },
	{ value: 'Completed', label: window.__('Completed'), icon: CheckCircle2, class: 'text-green-600' },
	{ value: 'Cancelled', label: window.__('Cancelled'), icon: Circle, class: 'text-gray-400' },
]

const priorityOptions = [
	{ value: 'Low', label: window.__('Low'), class: 'text-gray-500' },
	{ value: 'Medium', label: window.__('Medium'), class: 'text-yellow-600' },
	{ value: 'High', label: window.__('High'), class: 'text-orange-500' },
	{ value: 'Urgent', label: window.__('Urgent'), class: 'text-red-600' },
]

// Computed for current task timelogs
const currentTimelogs = computed(() => {
	if (!props.task?.name) return { timelogs: [], total_hours: 0 }
	return store.taskTimelogs[props.task.name] || { timelogs: [], total_hours: 0 }
})

// Watch for task changes
watch(() => props.task, async (newTask) => {
	if (newTask) {
		form.value = {
			subject: newTask.subject || '',
			project: newTask.project || '',
			status: newTask.status || 'Open',
			priority: newTask.priority || 'Medium',
			exp_end_date: newTask.exp_end_date || '',
			description: newTask.description || '',
		}
		setInitialFormSnapshot()
		// Load timelogs for existing task
		if (!props.isNew && newTask.name) {
			timelogsLoading.value = true
			try {
				await store.fetchTaskTimelogs(newTask.name)
			} finally {
				timelogsLoading.value = false
			}
		}
	}
}, { immediate: true })

// Reset form for new task
watch(() => props.isNew, (isNew) => {
	if (isNew) {
		const preset = store.drawerPreset || {}
		newTaskParentTask.value = preset.parent_task || null
		form.value = {
			subject: '',
			project: preset.project || (store.projects.length > 0 ? store.projects[0].name : ''),
			status: preset.status || 'Open',
			priority: preset.priority || 'Medium',
			exp_end_date: preset.exp_end_date || '',
			description: '',
		}
		errors.value = {}
		showSubtaskForm.value = false
		subtaskSubject.value = ''
		setInitialFormSnapshot()
	}
})

watch(
	[() => props.isOpen, () => store.drawerAction],
	([isOpen, action]) => {
		if (!isOpen) return
		if (!action) return
		if (action.type === 'timelog') {
			openTimeLogForm()
			store.clearDrawerAction()
		}
	},
	{ deep: true }
)

// Handle escape key
function handleKeydown(e) {
	if (e.key === 'Escape' && props.isOpen) {
		emit('close')
	}
}

async function createSubtask() {
	const subject = subtaskSubject.value.trim()
	if (!props.task?.name || !props.task?.project) return
	if (props.task.status === 'Completed' || props.task.status === 'Cancelled') return
	if (!subject) return

	try {
		await store.createTask({
			subject,
			project: props.task.project,
			parent_task: props.task.name,
			status: props.task.status,
			priority: props.task.priority,
			exp_end_date: props.task.exp_end_date || null,
		})
		subtaskSubject.value = ''
		showSubtaskForm.value = false
	} catch (e) {
		// handled by store/api
	}
}

onMounted(() => {
	document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
	document.removeEventListener('keydown', handleKeydown)
})

// Focus first input when drawer opens
watch(() => props.isOpen, async (isOpen) => {
	if (isOpen) {
		await nextTick()
		const firstInput = document.querySelector('.drawer-content input[type="text"]')
		if (firstInput) {
			firstInput.focus()
		}
	}
})

const isValid = computed(() => {
	return form.value.subject.trim() && form.value.project
})

const drawerTitle = computed(() => {
	if (props.isNew) return window.__('New Task')
	return window.__('Task Details')
})

async function handleSave() {
	errors.value = {}
	
	if (!form.value.subject.trim()) {
		errors.value.subject = window.__('Task name is required')
		return
	}
	
	if (!form.value.project) {
		errors.value.project = window.__('Project is required')
		return
	}
	
	saving.value = true
	
	try {
		if (props.isNew) {
			await store.createTask({
				subject: form.value.subject.trim(),
				project: form.value.project,
				parent_task: newTaskParentTask.value,
				status: form.value.status,
				priority: form.value.priority,
				exp_end_date: form.value.exp_end_date || null,
				description: form.value.description || null,
			})
			emit('created')
		} else {
			await store.updateTaskFull(props.task.name, {
				subject: form.value.subject.trim(),
				status: form.value.status,
				priority: form.value.priority,
				exp_end_date: form.value.exp_end_date || null,
				description: form.value.description || null,
			})
			emit('close')
		}
	} catch (err) {
		console.error('Failed to save task:', err)
	} finally {
		saving.value = false
	}
}

function handleOverlayClick(e) {
	if (e.target === e.currentTarget) {
		emit('close')
	}
}

// Timelog functions
function resetTimelogForm() {
	const today = new Date().toISOString().split('T')[0]
	timelogForm.value = {
		hours: '1',
		activity_type: store.activityTypes[0] || '',
		description: '',
		from_time: `${today}T08:00`,
	}
}

function openTimeLogForm() {
	resetTimelogForm()
	showTimeLogForm.value = true
	// Load activity types if not loaded
	if (store.activityTypes.length === 0) {
		store.fetchActivityTypes()
	}
}

async function handleSaveTimelog() {
	if (!timelogForm.value.hours || parseFloat(timelogForm.value.hours) <= 0) {
		if (window.frappe) {
			frappe.show_alert({ message: window.__('Please enter a valid number of hours'), indicator: 'red' })
		}
		return
	}
	
	if (!timelogForm.value.activity_type) {
		if (window.frappe) {
			frappe.show_alert({ message: window.__('Please select an activity type'), indicator: 'red' })
		}
		return
	}

	try {
		const hours = parseFloat(timelogForm.value.hours)
		// IMPORTANT: keep local time (do not use toISOString) to avoid timezone shift
		const fromStr = dayjs(timelogForm.value.from_time).format('YYYY-MM-DD HH:mm:ss')
		const toStr = dayjs(timelogForm.value.from_time).add(hours, 'hour').format('YYYY-MM-DD HH:mm:ss')
		
		await store.createTimelog({
			task: props.task.name,
			hours: hours,
			activity_type: timelogForm.value.activity_type,
			description: timelogForm.value.description,
			from_time: fromStr,
			to_time: toStr,
		})
		
		showTimeLogForm.value = false
		if (window.frappe) {
			frappe.show_alert({ message: 'Czas zapisany', indicator: 'green' })
		}
	} catch (error) {
		if (window.frappe) {
			frappe.show_alert({ message: window.__('Failed to save time entry'), indicator: 'red' })
		}
	}
}

async function handleDeleteTimelog(timelogName) {
if (!confirm(window.__('Are you sure you want to delete this time entry?'))) return
	
	try {
		await store.deleteTimelog(timelogName, props.task.name)
		if (window.frappe) {
			frappe.show_alert({ message: window.__('Time entry deleted'), indicator: 'green' })
		}
	} catch (error) {
		if (window.frappe) {
			frappe.show_alert({ message: window.__('Failed to delete time entry'), indicator: 'red' })
		}
	}
}

function formatDateTime(dateStr) {
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
</script>

<template>
	<Teleport to="body">
		<Transition name="drawer">
			<div
				v-if="isOpen"
				class="fixed inset-0 z-50 flex justify-end"
				@click="handleOverlayClick"
			>
				<!-- Overlay -->
				<div class="absolute inset-0 bg-black/30" @click="emit('close')"></div>

				<!-- Drawer panel -->
				<div 
					class="drawer-content relative w-full max-w-lg bg-white shadow-xl flex flex-col h-full md:h-auto md:max-h-[calc(100vh-2rem)] md:my-4 md:mr-4 md:rounded-lg overflow-hidden"
					role="dialog"
					aria-modal="true"
					:aria-labelledby="drawerTitle"
				>
					<!-- Header -->
					<div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
						<h2 class="text-lg font-semibold text-gray-900">{{ drawerTitle }}</h2>
						<button
							@click="emit('close')"
							class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
							aria-label="Zamknij"
						>
							<X class="w-5 h-5" />
						</button>
					</div>

					<!-- Content -->
					<div class="flex-1 overflow-y-auto p-4 space-y-4">
						<!-- Subject -->
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								{{ window.__('Task Name') }} <span class="text-red-500">*</span>
							</label>
							<input
								v-model="form.subject"
								type="text"
								:class="[
									'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
									errors.subject ? 'border-red-300' : 'border-gray-300'
								]"
								placeholder="{{ window.__('Enter task name...') }}"
							/>
							<p v-if="errors.subject" class="mt-1 text-sm text-red-600">{{ errors.subject }}</p>
						</div>

						<!-- Project -->
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								<Folder class="w-4 h-4 inline mr-1" />
								{{ window.__('Project') }} <span class="text-red-500">*</span>
							</label>
							<select
								v-model="form.project"
								:disabled="!isNew"
								:class="[
									'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
									errors.project ? 'border-red-300' : 'border-gray-300',
									!isNew && 'bg-gray-50 cursor-not-allowed'
								]"
							>
								<option value="">{{ window.__('Select project...') }}</option>
								<option 
									v-for="project in store.projects" 
									:key="project.name" 
									:value="project.name"
								>
									{{ project.project_name }}
								</option>
							</select>
							<p v-if="errors.project" class="mt-1 text-sm text-red-600">{{ errors.project }}</p>
							<p v-if="!isNew && task?.project_name" class="mt-1 text-sm text-gray-500">
								{{ task.project_name }}
							</p>
						</div>

						<!-- Status -->
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								{{ window.__('Status') }}
							</label>
							<div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
								<button
									v-for="option in statusOptions"
									:key="option.value"
									@click="form.status = option.value"
									:class="[
										'flex items-center gap-2 px-3 py-2 border rounded-lg text-sm transition-colors',
										form.status === option.value
											? 'border-blue-500 bg-blue-50 text-blue-700'
											: 'border-gray-200 hover:bg-gray-50'
									]"
								>
									<component :is="option.icon" :class="['w-4 h-4', option.class]" />
									{{ option.label }}
								</button>
							</div>
						</div>

						<!-- Priority -->
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								<Flag class="w-4 h-4 inline mr-1" />
								{{ window.__('Priority') }}
							</label>
							<div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
								<button
									v-for="option in priorityOptions"
									:key="option.value"
									@click="form.priority = option.value"
									:class="[
										'flex items-center gap-2 px-3 py-2 border rounded-lg text-sm transition-colors',
										form.priority === option.value
											? 'border-blue-500 bg-blue-50 text-blue-700'
											: 'border-gray-200 hover:bg-gray-50'
									]"
								>
									<Flag :class="['w-4 h-4', option.class]" />
									{{ option.label }}
								</button>
							</div>
						</div>

						<!-- Due date -->
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								<Calendar class="w-4 h-4 inline mr-1" />
								{{ window.__('Due Date') }}
							</label>
							<input
								v-model="form.exp_end_date"
								type="date"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							/>
						</div>

						<!-- Description -->
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								<FileText class="w-4 h-4 inline mr-1" />
								{{ window.__('Description') }}
							</label>
							<textarea
								v-model="form.description"
								rows="4"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
								placeholder="{{ window.__('Add task description...') }}"
							></textarea>
						</div>

						<!-- Subtasks (create) -->
						<div v-if="!isNew && task" class="pt-4 border-t border-gray-200">
							<div class="flex items-center justify-between mb-2">
								<h3 class="text-sm font-medium text-gray-700 flex items-center gap-2">
									<CheckCircle2 class="w-4 h-4" />
									{{ window.__('Subtasks') }}
								</h3>
								<button
									@click="showSubtaskForm = !showSubtaskForm"
									class="flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
								>
									<Plus class="w-3.5 h-3.5" />
									{{ window.__('Add') }}
								</button>
							</div>

							<div v-if="showSubtaskForm" class="bg-gray-50 rounded-lg p-3 space-y-3" @click.stop>
								<div>
									<label class="block text-xs font-medium text-gray-600 mb-1">{{ window.__('Subtask name') }}</label>
									<input
										v-model="subtaskSubject"
										type="text"
										class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
										placeholder="{{ window.__('e.g., Prepare documentation...') }}"
										@keydown.enter.prevent="createSubtask"
									/>
								</div>
								<div class="flex justify-end gap-2">
									<button
										@click="showSubtaskForm = false"
										class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-200 rounded transition-colors"
									>
										{{ window.__('Cancel') }}
									</button>
									<button
										@click="createSubtask"
										class="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
									>
										{{ window.__('Add') }}
									</button>
								</div>
							</div>
						</div>

						<!-- Time Logs (for existing tasks) -->
						<div v-if="!isNew && task" class="pt-4 border-t border-gray-200">
							<div class="flex items-center justify-between mb-3">
								<div>
									<h3 class="text-sm font-medium text-gray-700 flex items-center gap-2">
										<Clock class="w-4 h-4" />
										{{ window.__('Time Log') }}
									</h3>
									<p v-if="currentTimelogs.total_hours > 0" class="text-xs text-gray-500 mt-0.5">
										{{ window.__('Total') }}: {{ currentTimelogs.total_hours.toFixed(2) }} {{ window.__('hrs') }}.
									</p>
								</div>
								<button
									@click="openTimeLogForm"
									class="flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
								>
									<Plus class="w-3.5 h-3.5" />
									{{ window.__('Add') }}
								</button>
							</div>

							<!-- Time log form -->
							<div v-if="showTimeLogForm" class="bg-gray-50 rounded-lg p-3 mb-3 space-y-3">
								<div class="grid grid-cols-2 gap-3">
									<div>
										<label class="block text-xs font-medium text-gray-600 mb-1">{{ window.__('Hours') }} *</label>
										<input
											v-model="timelogForm.hours"
											type="number"
											step="0.25"
											min="0"
											max="24"
											class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
											placeholder="{{ window.__('e.g., 2.5') }}"
										/>
									</div>
									<div>
										<label class="block text-xs font-medium text-gray-600 mb-1">{{ window.__('Type') }} *</label>
										<select
											v-model="timelogForm.activity_type"
											class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
										>
											<option value="">{{ window.__('Select...') }}</option>
											<option v-for="type in store.activityTypes" :key="type" :value="type">
												{{ type }}
											</option>
										</select>
									</div>
								</div>
								<div>
									<label class="block text-xs font-medium text-gray-600 mb-1">{{ window.__('Date/Time') }}</label>
									<input
										v-model="timelogForm.from_time"
										type="datetime-local"
										class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
									/>
								</div>
								<div>
									<label class="block text-xs font-medium text-gray-600 mb-1">{{ window.__('Description') }}</label>
									<textarea
										v-model="timelogForm.description"
										rows="2"
										class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 resize-none"
										placeholder="{{ window.__('What did you do?') }}"
									></textarea>
								</div>
								<div class="flex justify-end gap-2">
									<button
										@click="showTimeLogForm = false"
										class="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-200 rounded transition-colors"
									>
										{{ window.__('Cancel') }}
									</button>
									<button
										@click="handleSaveTimelog"
										class="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
									>
										{{ window.__('Save') }}
									</button>
								</div>
							</div>

							<!-- Timelogs list -->
							<div v-if="timelogsLoading" class="text-center py-4">
								<Loader2 class="w-5 h-5 animate-spin mx-auto text-gray-400" />
							</div>
							<div v-else-if="currentTimelogs.timelogs.length === 0" class="text-sm text-gray-500 text-center py-4">
								{{ window.__('No time entries') }}
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
												<span class="font-semibold text-gray-900">{{ log.hours }} godz.</span>
												<span class="text-xs text-gray-500 bg-gray-200 px-1.5 py-0.5 rounded">{{ log.activity_type }}</span>
											</div>
											<p v-if="log.description" class="text-gray-600 text-xs mb-1">{{ log.description }}</p>
											<div class="flex items-center gap-2 text-xs text-gray-500">
												<span>{{ log.user_full_name }}</span>
												<span>•</span>
												<span>{{ formatDateTime(log.from_time) }}</span>
											</div>
										</div>
										<button
											@click="handleDeleteTimelog(log.timelog_name)"
											class="p-1 rounded hover:bg-red-100 text-gray-400 hover:text-red-600 transition-colors"
											title="{{ window.__('Delete entry') }}"
										>
											<Trash2 class="w-3.5 h-3.5" />
										</button>
									</div>
								</div>
							</div>
						</div>

						<!-- Task info (for existing tasks) -->
						<div v-if="!isNew && task" class="pt-4 border-t border-gray-200 text-sm text-gray-500 space-y-1">
							<p>ID: {{ task.name }}</p>
							<p v-if="task.modified">
								Ostatnia modyfikacja: {{ dayjs(task.modified).format('DD.MM.YYYY HH:mm') }}
							</p>
						</div>
					</div>

					<!-- Footer -->
					<div v-if="isDirty" class="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
						<div>
							<!-- TODO: Delete button -->
						</div>
						<div class="flex items-center gap-2">
							<button
								@click="emit('close')"
								class="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
							>
								{{ window.__('Cancel') }}
							</button>
							<button
								@click="handleSave"
								:disabled="saving || !isValid"
								class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
							>
								<Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
								<Save v-else class="w-4 h-4" />
								{{ isNew ? window.__('Create') : window.__('Save') }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
	transition: all 0.3s ease;
}

.drawer-enter-active .drawer-content,
.drawer-leave-active .drawer-content {
	transition: transform 0.3s ease;
}

.drawer-enter-from,
.drawer-leave-to {
	opacity: 0;
}

.drawer-enter-from .drawer-content,
.drawer-leave-to .drawer-content {
	transform: translateX(100%);
}

@media (max-width: 768px) {
	.drawer-content {
		max-width: 100%;
		border-radius: 0;
		margin: 0;
	}
}
</style>
