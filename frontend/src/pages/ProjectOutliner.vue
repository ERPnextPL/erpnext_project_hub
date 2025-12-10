<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/taskStore'
import TaskTree from '../components/TaskTree.vue'
import TaskDetailPanel from '../components/TaskDetailPanel.vue'
import QuickFilters from '../components/QuickFilters.vue'
import ProjectTeam from '../components/ProjectTeam.vue'
import MilestonePanel from '../components/MilestonePanel.vue'
import {
	ArrowLeft,
	ChevronDown,
	ChevronRight,
	Plus,
	LayoutList,
	Columns,
	GanttChart,
} from 'lucide-vue-next'

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
})

const router = useRouter()
const store = useTaskStore()

const activeView = ref('list')
const activeFilters = ref({
	status: null,
	priority: null,
	assignee: null,
})

onMounted(() => {
	store.fetchTasks(props.projectId)
})

function goBack() {
	router.push({ name: 'ProjectList' })
}

function handleFilterChange(filters) {
	activeFilters.value = filters
}

// Helper to get today's date in YYYY-MM-DD format
function getTodayDate() {
	const today = new Date()
	return today.toISOString().split('T')[0]
}

const filteredTasks = computed(() => {
	// Start with milestone-filtered tasks if a milestone filter is active
	let result = store.activeMilestoneFilter 
		? store.tasksFilteredByMilestone 
		: store.tasks

	// Apply additional filters
	if (activeFilters.value.status) {
		result = result.filter(t => t.status === activeFilters.value.status)
	}
	if (activeFilters.value.priority) {
		result = result.filter(t => t.priority === activeFilters.value.priority)
	}
	if (activeFilters.value.assignee) {
		result = result.filter(t => t._assign?.includes(activeFilters.value.assignee))
	}
	if (activeFilters.value.dueToday) {
		const today = getTodayDate()
		result = result.filter(t => t.exp_end_date === today)
	}

	return result
})

// Filtered task tree for display
const filteredTaskTree = computed(() => {
	if (store.activeMilestoneFilter) {
		return store.taskTreeFilteredByMilestone
	}
	return store.taskTree
})
</script>

<template>
	<div class="min-h-screen bg-gray-50 flex flex-col">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-14">
					<!-- Left: Back + Project name -->
					<div class="flex items-center gap-3">
						<button
							@click="goBack"
							class="p-1.5 -ml-1.5 rounded-md hover:bg-gray-100 text-gray-500"
						>
							<ArrowLeft class="w-5 h-5" />
						</button>
						<div v-if="store.project">
							<h1 class="text-lg font-semibold text-gray-900">
								{{ store.project.project_name }}
							</h1>
						</div>
						<div v-else class="h-5 w-40 bg-gray-200 rounded animate-pulse"></div>
					</div>

					<!-- Right: Team + View toggles -->
					<div class="flex items-center gap-3">
						<!-- Project Team -->
						<ProjectTeam :project-id="projectId" />
						
						<div class="flex items-center bg-gray-100 rounded-lg p-0.5">
							<button
								@click="activeView = 'list'"
								:class="[
									'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
									activeView === 'list'
										? 'bg-white text-gray-900 shadow-sm'
										: 'text-gray-600 hover:text-gray-900',
								]"
							>
								<LayoutList class="w-4 h-4" />
								List
							</button>
							<button
								@click="activeView = 'board'"
								:class="[
									'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
									activeView === 'board'
										? 'bg-white text-gray-900 shadow-sm'
										: 'text-gray-600 hover:text-gray-900',
								]"
							>
								<Columns class="w-4 h-4" />
								Board
							</button>
							<button
								@click="activeView = 'timeline'"
								:class="[
									'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
									activeView === 'timeline'
										? 'bg-white text-gray-900 shadow-sm'
										: 'text-gray-600 hover:text-gray-900',
								]"
							>
								<GanttChart class="w-4 h-4" />
								Timeline
							</button>
						</div>

						<a
							:href="`/app/project/${projectId}`"
							class="text-sm text-gray-500 hover:text-gray-700 ml-4"
						>
							Open in Desk →
						</a>
					</div>
				</div>
			</div>
		</header>

		<!-- Main content -->
		<div class="flex-1 flex overflow-hidden">
			<!-- Left sidebar: Milestones + Filters -->
			<aside class="w-64 bg-white border-r border-gray-200 flex-shrink-0 overflow-y-auto">
				<!-- Milestones Panel -->
				<MilestonePanel />
				
				<!-- Quick Filters -->
				<QuickFilters
					:project="store.project"
					@filter-change="handleFilterChange"
				/>
			</aside>

			<!-- Center: Task list -->
			<main class="flex-1 overflow-y-auto">
				<div v-if="store.loading" class="flex items-center justify-center py-12">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
				</div>

				<div v-else-if="activeView === 'list'">
					<TaskTree
						:tasks="filteredTasks"
						:project-id="projectId"
					/>
				</div>

				<div v-else-if="activeView === 'board'" class="p-6">
					<p class="text-gray-500 text-center py-12">
						Kanban board view coming soon...
					</p>
				</div>

				<div v-else-if="activeView === 'timeline'" class="p-6">
					<p class="text-gray-500 text-center py-12">
						Timeline/Gantt view coming soon...
					</p>
				</div>
			</main>

			<!-- Right panel: Task details -->
			<Transition name="slide-over">
				<TaskDetailPanel
					v-if="store.selectedTask"
					:task="store.selectedTask"
					@close="store.clearSelection"
				/>
			</Transition>
		</div>
	</div>
</template>
