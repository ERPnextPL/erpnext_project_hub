<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/taskStore'
import TaskTree from '../components/TaskTree.vue'
import TaskDetailPanel from '../components/TaskDetailPanel.vue'
import QuickFilters from '../components/QuickFilters.vue'
import ProjectTeam from '../components/ProjectTeam.vue'
import MilestonePanel from '../components/MilestonePanel.vue'
import ProjectInfoPanel from '../components/ProjectInfoPanel.vue'
import KanbanBoard from '../components/KanbanBoard.vue'
import TimelineView from '../components/TimelineView.vue'
import {
	ArrowLeft,
	ChevronDown,
	ChevronRight,
	Plus,
	LayoutList,
	Columns,
	GanttChart,
	PanelLeftClose,
	PanelLeft,
	CheckCircle2,
	Circle,
	Clock,
} from 'lucide-vue-next'
import OutlinerNav from '../components/OutlinerNav.vue'
import { translate } from '../utils/translation'

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
})

const router = useRouter()
const store = useTaskStore()

const activeView = ref('list')
const sidebarCollapsed = ref(false)
const activeFilters = ref({
	status: [], // Array for multiselect
	priority: [], // Array for multiselect
	assignee: null,
	dueToday: false,
})

// Project progress statistics
const projectStats = computed(() => {
	const total = store.tasks.length
	if (total === 0) return { total: 0, completed: 0, inProgress: 0, open: 0, percent: 0 }
	
	const completed = store.tasks.filter(t => t.status === 'Completed').length
	const cancelled = store.tasks.filter(t => t.status === 'Cancelled').length
	const inProgress = store.tasks.filter(t => t.status === 'Working' || t.status === 'Pending Review').length
	const open = store.tasks.filter(t => t.status === 'Open').length
	
	// Calculate percent excluding cancelled tasks
	const activeTotal = total - cancelled
	const percent = activeTotal > 0 ? Math.round((completed / activeTotal) * 100) : 0
	
	return { total, completed, inProgress, open, cancelled, percent }
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

function handleTaskClick(task) {
	store.selectTask(task)
}

// Helper to get today's date in YYYY-MM-DD format
function getTodayDate() {
	const today = new Date()
	return today.toISOString().split('T')[0]
}

// Flattened tasks with levels for proper indentation
const flattenedTasksWithFilters = computed(() => {
	// Start with milestone-filtered tasks if active
	let baseTasks = store.activeMilestoneFilter 
		? store.tasksFilteredByMilestone 
		: store.tasks
	
	// Build flattened tree from filtered tasks
	const buildFlattenedTree = (tasks) => {
		const taskMap = new Map(tasks.map(t => [t.name, t]))
		const roots = tasks.filter(t => !t.parent_task || !taskMap.has(t.parent_task))
		const result = []
		
		const addWithChildren = (task, level = 0) => {
			result.push({ ...task, level })
			if (store.expandedTasks.has(task.name)) {
				const children = tasks.filter(t => t.parent_task === task.name)
				children.forEach(child => addWithChildren(child, level + 1))
			}
		}
		
		roots.forEach(task => addWithChildren(task))
		return result
	}
	
	let result = buildFlattenedTree(baseTasks)

	// Apply additional filters
	if (activeFilters.value.status && activeFilters.value.status.length > 0) {
		result = result.filter(t => activeFilters.value.status.includes(t.status))
	}
	
	if (activeFilters.value.priority && activeFilters.value.priority.length > 0) {
		result = result.filter(t => activeFilters.value.priority.includes(t.priority))
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
</script>

<template>
	<div class="min-h-screen bg-gray-50 flex flex-col">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="px-4 sm:px-6 lg:px-8">
				<div class="flex flex-wrap items-center justify-between gap-3 min-h-[56px]">
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
					<div class="flex items-center gap-3 flex-wrap justify-end">
						<!-- Project Team -->
						<ProjectTeam :project-id="projectId" />
						<OutlinerNav />
						
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
								{{ translate('List') }}
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
								{{ translate('Board') }}
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
							{{ translate('Open in Desk') }} →
						</a>
					</div>
				</div>
			</div>
		</header>

		<!-- Main content -->
		<div class="flex-1 flex overflow-hidden">
			<!-- Left sidebar: Milestones + Filters (collapsible) -->
			<!-- Sidebar toggle button (visible when collapsed) -->
			<button
				v-if="sidebarCollapsed"
				@click="sidebarCollapsed = false"
				class="flex-shrink-0 bg-white border-r border-gray-200 p-2 hover:bg-gray-50 transition-colors"
				:title="translate('Show sidebar')"
			>
				<PanelLeft class="w-4 h-4 text-gray-500" />
			</button>
			
			<aside 
				v-else
				class="bg-white border-r border-gray-200 flex-shrink-0 overflow-y-auto w-64 relative"
			>
				<!-- Sidebar toggle button (pinned to right edge) -->
				<button
					@click="sidebarCollapsed = true"
					class="absolute right-0 top-20 z-10 bg-white border border-gray-200 border-r-0 rounded-l-md p-1 shadow-sm hover:bg-gray-50"
					title="Ukryj panel boczny"
				>
					<PanelLeftClose class="w-4 h-4 text-gray-500" />
				</button>
				
				<div class="w-64">
					<!-- Milestones Panel -->
					<MilestonePanel />
					
					<!-- Quick Filters -->
					<QuickFilters
						:project="store.project"
						@filter-change="handleFilterChange"
					/>
				</div>
			</aside>

			<!-- Center: Task list -->
			<main class="flex-1 overflow-y-auto">
				<!-- Project Information Panel -->
				<ProjectInfoPanel v-if="store.project && !store.loading" :project="store.project" />
				

				<div v-if="store.loading" class="flex items-center justify-center py-12">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
				</div>

				<div v-else-if="activeView === 'list'">
					<TaskTree
						:tasks="flattenedTasksWithFilters"
						:project-id="projectId"
					/>
				</div>

				<div v-else-if="activeView === 'board'" class="h-full">
					<KanbanBoard
						:tasks="flattenedTasksWithFilters"
						:project-id="projectId"
						@task-click="handleTaskClick"
					/>
				</div>

				<div v-else-if="activeView === 'timeline'" class="h-full">
					<TimelineView
						:tasks="flattenedTasksWithFilters"
						:project-id="projectId"
						@task-click="handleTaskClick"
					/>
				</div>
			</main>

			<!-- Right panel: Task details with overlay -->
			<Transition name="slide-over">
				<div v-if="store.selectedTask" class="fixed inset-0 z-30 flex justify-end">
					<!-- Overlay - click to close -->
					<div 
						class="absolute inset-0 bg-black/20"
						@click="store.clearSelection"
					></div>
					<!-- Panel -->
					<TaskDetailPanel
						:task="store.selectedTask"
						@close="store.clearSelection"
						class="relative z-10"
					/>
				</div>
			</Transition>
		</div>
	</div>
</template>
