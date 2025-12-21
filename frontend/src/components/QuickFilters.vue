<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import {
	Filter,
	Circle,
	Clock,
	CheckCircle2,
	AlertCircle,
	User,
	Flag,
	Calendar,
	X,
} from 'lucide-vue-next'

const props = defineProps({
	project: {
		type: Object,
		default: null,
	},
})

const emit = defineEmits(['filter-change'])

const store = useTaskStore()
const activeStatus = ref([]) // Array for multiselect
const activePriority = ref([]) // Array for multiselect
const activeAssignee = ref(null)
const myTasksActive = ref(false)
const dueTodayActive = ref(false)

const disabledStatuses = ['Template']

// Get current user from Frappe session
const currentUser = computed(() => {
	return window.frappe?.session?.user || ''
})

// Load metadata on mount
onMounted(async () => {
	if (store.taskStatuses.length === 0) {
		await store.fetchTaskStatuses()
	}
	if (store.taskPriorities.length === 0) {
		await store.fetchTaskPriorities()
	}
	
	// Set default status filters - all except Cancelled and Closed
	if (activeStatus.value.length === 0) {
		activeStatus.value = store.taskStatuses.filter(
			status => status !== 'Cancelled' && status !== 'Closed' && status !== 'Completed' && !disabledStatuses.includes(status)
		)
		emitFilters()
	}
})

// Icon and color mapping
const statusIconMap = {
	'Open': { icon: Circle, class: 'text-blue-600' },
	'Working': { icon: Clock, class: 'text-amber-600' },
	'Pending Review': { icon: AlertCircle, class: 'text-purple-600' },
	'Completed': { icon: CheckCircle2, class: 'text-green-600' },
	'Overdue': { icon: AlertCircle, class: 'text-red-600' },
	'Cancelled': { icon: Circle, class: 'text-gray-400' },
}

const priorityColorMap = {
	'Urgent': 'text-red-600',
	'High': 'text-orange-500',
	'Medium': 'text-yellow-500',
	'Low': 'text-gray-400',
}

const statuses = computed(() => {
	return store.taskStatuses.map(status => {
		const config = statusIconMap[status] || { icon: Circle, class: 'text-gray-500' }
		return {
			value: status,
			label: status === 'Working' ? window.__('Working') : (status === 'Pending Review' ? window.__('Pending Review') : (status === 'Template' ? window.__('Template') : status)),
			icon: config.icon,
			class: config.class,
			disabled: disabledStatuses.includes(status),
		}
	})
})

const priorities = computed(() => {
	return store.taskPriorities.map(priority => ({
		value: priority,
		label: priority,
		class: priorityColorMap[priority] || 'text-gray-400'
	}))
})

const hasActiveFilters = computed(() => {
	return (activeStatus.value && activeStatus.value.length > 0) || 
			(activePriority.value && activePriority.value.length > 0) || 
			activeAssignee.value || 
			myTasksActive.value || 
			dueTodayActive.value
})

function toggleStatus(status) {
	if (disabledStatuses.includes(status)) return
	const index = activeStatus.value.indexOf(status)
	if (index > -1) {
		activeStatus.value.splice(index, 1)
	} else {
		activeStatus.value.push(status)
	}
	emitFilters()
}

function togglePriority(priority) {
	const index = activePriority.value.indexOf(priority)
	if (index > -1) {
		activePriority.value.splice(index, 1)
	} else {
		activePriority.value.push(priority)
	}
	emitFilters()
}

function toggleMyTasks() {
	myTasksActive.value = !myTasksActive.value
	if (myTasksActive.value) {
		activeAssignee.value = currentUser.value
	} else {
		activeAssignee.value = null
	}
	emitFilters()
}

function toggleDueToday() {
	dueTodayActive.value = !dueTodayActive.value
	emitFilters()
}

function clearFilters() {
	activeStatus.value = []
	activePriority.value = []
	activeAssignee.value = null
	myTasksActive.value = false
	dueTodayActive.value = false
	emitFilters()
}

function emitFilters() {
	emit('filter-change', {
		status: activeStatus.value,
		priority: activePriority.value,
		assignee: activeAssignee.value,
		dueToday: dueTodayActive.value,
	})
}

</script>

<template>
	<div class="p-4 space-y-6">
		<!-- Header -->
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-2 text-sm font-medium text-gray-700">
				<Filter class="w-4 h-4" />
				{{ window.__('Filters') }}
			</div>
			<button
				v-if="hasActiveFilters"
				@click="clearFilters"
				class="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
			>
				<X class="w-3 h-3" />
				{{ window.__('Clear') }}
			</button>
		</div>

		<!-- Quick filters -->
		<div class="space-y-1">
			<!-- My Tasks -->
			<button
				@click="toggleMyTasks"
				:class="[
					'w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md text-left',
					myTasksActive ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-100',
				]"
			>
				<User :class="['w-4 h-4', myTasksActive ? 'text-blue-600' : 'text-gray-400']" />
				{{ window.__('My Tasks') }}
			</button>

			<!-- Due Today -->
			<button
				@click="toggleDueToday"
				:class="[
					'w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md text-left',
					dueTodayActive ? 'bg-amber-50 text-amber-700' : 'text-gray-700 hover:bg-gray-100',
				]"
			>
				<Calendar :class="['w-4 h-4', dueTodayActive ? 'text-amber-600' : 'text-gray-400']" />
				{{ window.__('Due Today') }}
			</button>

			<!-- Overdue -->
			<button
				@click="toggleStatus('Overdue')"
				:class="[
					'w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md text-left',
					activeStatus.includes('Overdue') ? 'bg-red-50 text-red-700' : 'text-gray-700 hover:bg-gray-100',
				]"
			>
				<AlertCircle class="w-4 h-4 text-red-500" />
				Overdue
			</button>
		</div>

		<hr class="border-gray-200" />

		<!-- Status filter -->
		<div>
			<h3 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
				Status
			</h3>
			<div class="space-y-1">
				<button
					v-for="status in statuses"
					:key="status.value"
					@click="toggleStatus(status.value)"
					:class="[
						'w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-left relative',
						status.disabled ? 'opacity-50 cursor-not-allowed' : '',
						activeStatus.includes(status.value)
							? 'bg-blue-50 text-blue-700'
							: 'text-gray-700 hover:bg-gray-100',
					]"
				>
					<component :is="status.icon" :class="['w-4 h-4', status.class]" />
					{{ status.label }}
					<!-- Check indicator for multiselect -->
					<span v-if="activeStatus.includes(status.value) && !status.disabled" class="ml-auto">
						<svg class="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
						</svg>
					</span>
				</button>
			</div>
		</div>

		<hr class="border-gray-200" />

		<!-- Priority filter -->
		<div>
			<h3 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
				Priorytet
			</h3>
			<div class="space-y-1">
				<button
					v-for="priority in priorities"
					:key="priority.value"
					@click="togglePriority(priority.value)"
					:class="[
						'w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-left relative',
						activePriority.includes(priority.value)
							? 'bg-blue-50 text-blue-700'
							: 'text-gray-700 hover:bg-gray-100',
					]"
				>
					<Flag :class="['w-4 h-4', priority.class]" />
					{{ priority.label }}
					<!-- Check indicator for multiselect -->
					<span v-if="activePriority.includes(priority.value)" class="ml-auto">
						<svg class="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
						</svg>
					</span>
				</button>
			</div>
		</div>

		<!-- Project info -->
		<div v-if="project" class="pt-4 border-t border-gray-200">
			<h3 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
				{{ window.__('Project') }}
			</h3>
			<div class="text-sm text-gray-700">
				<p class="font-medium">{{ project.project_name }}</p>
				<p v-if="project.percent_complete !== null" class="text-gray-500 mt-1">
					{{ project.percent_complete }}% {{ window.__('complete') }}
				</p>
			</div>
		</div>
	</div>
</template>
