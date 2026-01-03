<script setup>
import { computed } from 'vue'
import { useMyTasksStore } from '../../stores/myTasksStore'
import {
	Circle,
	Clock,
	CheckCircle2,
	AlertCircle,
	Flag,
	Calendar,
	CalendarDays,
	X,
	Folder,
} from 'lucide-vue-next'

const store = useMyTasksStore()

// Icon and color mapping for statuses
const statusConfig = {
	'Open': { icon: Circle, class: 'text-blue-600', bg: 'bg-blue-50' },
	'Working': { icon: Clock, class: 'text-amber-600', bg: 'bg-amber-50' },
	'Pending Review': { icon: AlertCircle, class: 'text-purple-600', bg: 'bg-purple-50' },
	'Completed': { icon: CheckCircle2, class: 'text-green-600', bg: 'bg-green-50' },
	'Overdue': { icon: AlertCircle, class: 'text-red-600', bg: 'bg-red-50' },
	'Cancelled': { icon: Circle, class: 'text-gray-400', bg: 'bg-gray-50' },
}

const priorityConfig = {
	'Urgent': { class: 'text-red-600', bg: 'bg-red-50' },
	'High': { class: 'text-orange-500', bg: 'bg-orange-50' },
	'Medium': { class: 'text-yellow-600', bg: 'bg-yellow-50' },
	'Low': { class: 'text-gray-500', bg: 'bg-gray-50' },
}

const dueFilterOptions = [
	{ value: 'today', label: window.__('Today'), icon: Calendar },
	{ value: 'week', label: window.__('This week'), icon: CalendarDays },
	{ value: 'overdue', label: window.__('Overdue'), icon: AlertCircle },
]

const statuses = computed(() => {
	return store.statuses.map(status => ({
		value: status,
		label: status === 'Working' ? window.__('Working') : 
			   status === 'Pending Review' ? window.__('Pending Review') :
			   status === 'Completed' ? window.__('Completed') :
			   status === 'Cancelled' ? window.__('Cancelled') :
			   status === 'Overdue' ? window.__('Overdue') :
			   status === 'Open' ? window.__('Open') : status,
		...statusConfig[status] || { icon: Circle, class: 'text-gray-500', bg: 'bg-gray-50' }
	}))
})

const priorities = computed(() => {
	return store.priorities.map(priority => ({
		value: priority,
		label: priority === 'Urgent' ? window.__('Urgent') :
			   priority === 'High' ? window.__('High') :
			   priority === 'Medium' ? window.__('Medium') :
			   priority === 'Low' ? window.__('Low') : priority,
		...priorityConfig[priority] || { class: 'text-gray-500', bg: 'bg-gray-50' }
	}))
})

function isStatusActive(status) {
	return store.filters.status.includes(status)
}

function isPriorityActive(priority) {
	return store.filters.priority.includes(priority)
}

function isDueFilterActive(filter) {
	return store.filters.dueFilter === filter
}

function toggleDueFilter(filter) {
	if (store.filters.dueFilter === filter) {
		store.setFilter('dueFilter', null)
	} else {
		store.setFilter('dueFilter', filter)
	}
	store.fetchTasks()
}

function setProjectFilter(project) {
	store.setFilter('project', project || null)
	store.fetchTasks()
}
</script>

<template>
	<div class="space-y-4">
		<!-- View options -->
		<div>
			<h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ window.__('View') }}</h4>
			<div class="flex flex-wrap gap-2">
				<button
					@click="store.toggleViewOption('groupByStatus')"
					:class="[
						'px-3 py-1.5 text-sm rounded-full border transition-colors',
						store.viewOptions.groupByStatus
							? 'bg-blue-50 border-blue-200 text-blue-700'
							: 'border-gray-200 text-gray-600 hover:bg-gray-50'
					]"
				>
					{{ window.__('Group by status') }}
				</button>
			</div>
		</div>

		<!-- Due date presets -->
		<div>
			<h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ window.__('Due date') }}</h4>
			<div class="flex flex-wrap gap-2">
				<button
					v-for="option in dueFilterOptions"
					:key="option.value"
					@click="toggleDueFilter(option.value)"
					:class="[
						'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full border transition-colors',
						isDueFilterActive(option.value)
							? 'bg-blue-50 border-blue-200 text-blue-700'
							: 'border-gray-200 text-gray-600 hover:bg-gray-50'
					]"
				>
					<component 
						:is="option.icon" 
						:class="['w-3.5 h-3.5', isDueFilterActive(option.value) ? 'text-blue-600' : 'text-gray-400']" 
					/>
					{{ option.label }}
				</button>
				<button
					v-if="store.filters.dueFilter"
					@click="store.setFilter('dueFilter', null)"
					class="flex items-center gap-1 px-2 py-1.5 text-sm text-gray-500 hover:text-gray-700"
				>
					<X class="w-3.5 h-3.5" />
				</button>
			</div>
		</div>

		<!-- Status filter -->
		<div>
			<h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ window.__('Status') }}</h4>
			<div class="flex flex-wrap gap-2">
				<button
					v-for="status in statuses"
					:key="status.value"
					@click="store.toggleStatusFilter(status.value)"
					:class="[
						'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full border transition-colors',
						isStatusActive(status.value)
							? `${status.bg} border-current ${status.class}`
							: 'border-gray-200 text-gray-600 hover:bg-gray-50'
					]"
				>
					<component 
						:is="status.icon" 
						:class="['w-3.5 h-3.5', isStatusActive(status.value) ? status.class : 'text-gray-400']" 
					/>
					{{ status.label }}
				</button>
			</div>
		</div>

		<!-- Priority filter -->
		<div>
			<h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ window.__('Priority') }}</h4>
			<div class="flex flex-wrap gap-2">
				<button
					v-for="priority in priorities"
					:key="priority.value"
					@click="store.togglePriorityFilter(priority.value)"
					:class="[
						'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full border transition-colors',
						isPriorityActive(priority.value)
							? `${priority.bg} border-current ${priority.class}`
							: 'border-gray-200 text-gray-600 hover:bg-gray-50'
					]"
				>
					<Flag 
						:class="['w-3.5 h-3.5', isPriorityActive(priority.value) ? priority.class : 'text-gray-400']" 
					/>
					{{ priority.label }}
				</button>
			</div>
		</div>

		<!-- Project filter -->
		<div v-if="store.projects.length > 0">
			<h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ window.__('Project') }}</h4>
			<div class="flex flex-wrap gap-2">
				<button
					@click="setProjectFilter(null)"
					:class="[
						'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full border transition-colors',
						!store.filters.project
							? 'bg-blue-50 border-blue-200 text-blue-700'
							: 'border-gray-200 text-gray-600 hover:bg-gray-50'
					]"
				>
					{{ window.__('All') }}
				</button>
				<button
					v-for="project in store.projects"
					:key="project.name"
					@click="setProjectFilter(project.name)"
					:class="[
						'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-full border transition-colors',
						store.filters.project === project.name
							? 'bg-blue-50 border-blue-200 text-blue-700'
							: 'border-gray-200 text-gray-600 hover:bg-gray-50'
					]"
				>
					<Folder class="w-3.5 h-3.5" />
					{{ project.project_name }}
					<span class="text-xs text-gray-400">({{ project.task_count }})</span>
				</button>
			</div>
		</div>

		<!-- Clear all -->
		<div v-if="store.hasActiveFilters" class="pt-2 border-t border-gray-200">
			<button
				@click="store.clearFilters()"
				class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
			>
				<X class="w-3.5 h-3.5" />
				{{ window.__('Clear all filters') }}
			</button>
		</div>
	</div>
</template>
