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
const activeStatus = ref(null)
const activePriority = ref(null)
const activeAssignee = ref(null)
const myTasksActive = ref(false)
const dueTodayActive = ref(false)

// Get current user from Frappe session
const currentUser = computed(() => {
	return window.frappe?.session?.user || ''
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
			label: status === 'Working' ? 'In Progress' : (status === 'Pending Review' ? 'Review' : status),
			icon: config.icon,
			class: config.class
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
	return activeStatus.value || activePriority.value || activeAssignee.value || myTasksActive.value || dueTodayActive.value
})

function toggleStatus(status) {
	activeStatus.value = activeStatus.value === status ? null : status
	emitFilters()
}

function togglePriority(priority) {
	activePriority.value = activePriority.value === priority ? null : priority
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
	activeStatus.value = null
	activePriority.value = null
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
				Filters
			</div>
			<button
				v-if="hasActiveFilters"
				@click="clearFilters"
				class="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
			>
				<X class="w-3 h-3" />
				Clear
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
				My Tasks
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
				Due Today
			</button>

			<!-- Overdue -->
			<button
				@click="toggleStatus('Overdue')"
				:class="[
					'w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md text-left',
					activeStatus === 'Overdue' ? 'bg-red-50 text-red-700' : 'text-gray-700 hover:bg-gray-100',
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
						'w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-left',
						activeStatus === status.value
							? 'bg-blue-50 text-blue-700'
							: 'text-gray-700 hover:bg-gray-100',
					]"
				>
					<component :is="status.icon" :class="['w-4 h-4', status.class]" />
					{{ status.label }}
				</button>
			</div>
		</div>

		<hr class="border-gray-200" />

		<!-- Priority filter -->
		<div>
			<h3 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
				Priority
			</h3>
			<div class="space-y-1">
				<button
					v-for="priority in priorities"
					:key="priority.value"
					@click="togglePriority(priority.value)"
					:class="[
						'w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-left',
						activePriority === priority.value
							? 'bg-blue-50 text-blue-700'
							: 'text-gray-700 hover:bg-gray-100',
					]"
				>
					<Flag :class="['w-4 h-4', priority.class]" />
					{{ priority.label }}
				</button>
			</div>
		</div>

		<!-- Project info -->
		<div v-if="project" class="pt-4 border-t border-gray-200">
			<h3 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
				Project
			</h3>
			<div class="text-sm text-gray-700">
				<p class="font-medium">{{ project.project_name }}</p>
				<p v-if="project.percent_complete !== null" class="text-gray-500 mt-1">
					{{ project.percent_complete }}% complete
				</p>
			</div>
		</div>
	</div>
</template>
