<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { useTaskStore } from "../stores/taskStore";
import TaskTree from "../components/TaskTree.vue";
import TaskDetailPanel from "../components/TaskDetailPanel.vue";
import QuickFilters from "../components/QuickFilters.vue";
import ProjectTeam from "../components/ProjectTeam.vue";
import MilestonePanel from "../components/MilestonePanel.vue";
import ProjectInfoPanel from "../components/ProjectInfoPanel.vue";
import KanbanBoard from "../components/KanbanBoard.vue";
import TimelineView from "../components/TimelineView.vue";
import { ArrowLeft, Filter, LayoutList, Columns, GanttChart } from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import { translate } from "../utils/translation";

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
});

const router = useRouter();
const store = useTaskStore();

const activeView = ref("list");
const sidebarCollapsed = ref(true); // Domyślnie zwinięty
// Domyślne filtry: wszystkie statusy poza Completed, Cancelled, Closed
const activeFilters = ref({
	status: ["Open", "Working", "Pending Review", "Overdue"], // Domyślne statusy
	priority: [], // Array for multiselect
	assignee: null,
	dueToday: false,
	overdue: false, // Nowy filtr dla przeterminowanych zadań
	search: "",
});


onMounted(() => {
	store.fetchTasks(props.projectId, activeFilters.value);
});

function goBack() {
	router.push({ name: "ProjectList" });
}

function handleFilterChange(filters) {
	activeFilters.value = { ...activeFilters.value, ...filters };
	store.fetchTasks(props.projectId, activeFilters.value);
}

function handleTaskClick(task) {
	store.selectTask(task);
}

// Helper to get today's date in YYYY-MM-DD format
function getTodayDate() {
	const today = new Date();
	return today.toISOString().split("T")[0];
}

// Flattened tasks with levels for proper indentation
const flattenedTasksWithFilters = computed(() => {
	// Start with milestone-filtered tasks if active
	let baseTasks = store.activeMilestoneFilter ? store.tasksFilteredByMilestone : store.tasks;

	// Build flattened tree from filtered tasks
	const buildFlattenedTree = (tasks) => {
		const taskMap = new Map(tasks.map((t) => [t.name, t]));
		const roots = tasks.filter((t) => !t.parent_task || !taskMap.has(t.parent_task));
		const result = [];

		const addWithChildren = (task, level = 0) => {
			result.push({ ...task, level });
			if (store.expandedTasks.has(task.name)) {
				const children = tasks.filter((t) => t.parent_task === task.name);
				children.forEach((child) => addWithChildren(child, level + 1));
			}
		};

		roots.forEach((task) => addWithChildren(task));
		return result;
	};

	let result = buildFlattenedTree(baseTasks);

	// Apply additional filters
	if (activeFilters.value.status && activeFilters.value.status.length > 0) {
		result = result.filter((t) => activeFilters.value.status.includes(t.status));
	}

	if (activeFilters.value.priority && activeFilters.value.priority.length > 0) {
		result = result.filter((t) => activeFilters.value.priority.includes(t.priority));
	}
	if (activeFilters.value.assignee) {
		result = result.filter((t) => t._assign?.includes(activeFilters.value.assignee));
	}
	if (activeFilters.value.dueToday) {
		const today = getTodayDate();
		result = result.filter((t) => t.exp_end_date === today);
	}
	// Filtr przeterminowanych zadań (według daty, nie statusu)
	if (activeFilters.value.overdue) {
		const today = getTodayDate();
		result = result.filter((t) => {
			return (
				t.exp_end_date &&
				t.exp_end_date < today &&
				t.status !== "Completed" &&
				t.status !== "Cancelled"
			);
		});
	}

	return result;
});
</script>

<template>
	<div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
		<!-- Header -->
		<header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-20">
			<div class="px-4 sm:px-6 lg:px-8">
				<div class="flex flex-wrap items-center justify-between gap-3 min-h-[56px]">
					<!-- Left: Back + Project name -->
					<div class="flex items-center gap-3">
						<button
							@click="goBack"
							class="p-1.5 -ml-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
						>
							<ArrowLeft class="w-5 h-5" />
						</button>
						<div v-if="store.project">
							<h1 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
								{{ store.project.project_name }}
							</h1>
						</div>
						<div v-else class="h-5 w-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
					</div>

					<!-- Right: Theme + Team + View toggles -->
					<div class="flex items-center gap-3 flex-wrap justify-end">
						<!-- Project Team -->
						<ProjectTeam :project-id="projectId" />
						<OutlinerNav />

						<div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
							<button
								@click="activeView = 'list'"
								:class="[
									'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
									activeView === 'list'
										? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
										: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100',
								]"
							>
								<LayoutList class="w-4 h-4" />
								{{ translate("List") }}
							</button>
							<button
								@click="activeView = 'board'"
								:class="[
									'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
									activeView === 'board'
										? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
										: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100',
								]"
							>
								<Columns class="w-4 h-4" />
								{{ translate("Board") }}
							</button>
							<button
								@click="activeView = 'timeline'"
								:class="[
									'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
									activeView === 'timeline'
										? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
										: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100',
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
							{{ translate("Open in Desk") }} →
						</a>
					</div>
				</div>
			</div>
		</header>

		<!-- Main content -->
		<div class="flex-1 flex overflow-hidden relative">
			<!-- Left sidebar: Milestones + Filters (collapsible) -->
			<aside
				v-if="!sidebarCollapsed"
				class="bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 overflow-y-auto w-64 relative"
			>
				<div class="w-64">
					<!-- Milestones Panel -->
					<MilestonePanel />

					<!-- Quick Filters -->
					<QuickFilters :project="store.project" @filter-change="handleFilterChange" />
				</div>
			</aside>

			<!-- Elegant sidebar toggle button (ClickUp/Jira style) -->
			<button
				@click="sidebarCollapsed = !sidebarCollapsed"
				:class="[
					'absolute top-1/2 -translate-y-1/2 z-20 transition-all duration-200',
					'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500',
					'shadow-md hover:shadow-lg',
					'rounded-r-md',
					'flex items-center justify-center',
					'group',
					'w-6 h-16',
					sidebarCollapsed ? 'left-0' : 'left-64'
				]"
				:title="sidebarCollapsed ? translate('Show filters') : translate('Hide filters')"
			>
				<Filter
					class="w-4 h-4 transition-colors"
					:class="[
						sidebarCollapsed
							? 'text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200'
							: 'text-blue-600 dark:text-blue-300 group-hover:text-blue-700 dark:group-hover:text-blue-200'
					]"
				/>
			</button>

			<!-- Center: Task list -->
			<main class="flex-1 overflow-y-auto">
				<!-- Project Information Panel -->
				<ProjectInfoPanel
					v-if="store.project && !store.loading"
					:project="store.project"
				/>

				<div v-if="store.loading" class="flex items-center justify-center py-12">
					<div
						class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
					></div>
				</div>

				<div v-else-if="activeView === 'list'">
					<TaskTree :tasks="flattenedTasksWithFilters" :project-id="projectId" />
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
					<div class="absolute inset-0 bg-black/20" @click="store.clearSelection"></div>
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
