<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useDebounceFn, useWindowSize } from "@vueuse/core";
import { useTaskStore } from "../stores/taskStore";
import TaskTree from "../components/TaskTree.vue";
import TaskDetailPanel from "../components/TaskDetailPanel.vue";
import ProjectTaskCardMobile from "../components/ProjectTaskCardMobile.vue";
import QuickFilters from "../components/QuickFilters.vue";
import ProjectTeam from "../components/ProjectTeam.vue";
import MilestonePanel from "../components/MilestonePanel.vue";
import ProjectInfoPanel from "../components/ProjectInfoPanel.vue";
import KanbanBoard from "../components/KanbanBoard.vue";
import TimelineView from "../components/TimelineView.vue";
import QuickAddTask from "../components/QuickAddTask.vue";
import {
	ArrowLeft,
	Filter,
	Search,
	X,
	RefreshCw,
	LayoutList,
	Columns,
	GanttChart,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import BackToDeskButton from "../components/BackToDeskButton.vue";
import { translate } from "../utils/translation";

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
});

const router = useRouter();
const store = useTaskStore();

const { width } = useWindowSize();
const isMobile = computed(() => width.value < 768);

const activeView = ref("list");
const listMode = ref("flat");
const sidebarCollapsed = ref(true); // Domyślnie zwinięty
const searchInput = ref("");
// Domyślne filtry: wszystkie statusy poza Completed, Cancelled, Closed
const activeFilters = ref({
	status: ["Open", "Working", "Pending Review", "Overdue"], // Domyślne statusy
	priority: [], // Array for multiselect
	assignee: null,
	dueToday: false,
	overdue: false, // Nowy filtr dla przeterminowanych zadań
	search: "",
});

const hasActiveFilters = computed(() => {
	return (
		activeFilters.value.priority.length > 0 ||
		activeFilters.value.assignee ||
		activeFilters.value.dueToday ||
		activeFilters.value.overdue ||
		activeFilters.value.search
	);
});

const debouncedSearch = useDebounceFn((value) => {
	activeFilters.value.search = value;
	store.fetchTasks(props.projectId, activeFilters.value);
}, 300);

watch(searchInput, (value) => {
	debouncedSearch(value);
});

onMounted(() => {
	store.fetchTasks(props.projectId, activeFilters.value);
});

watch(
	() => store.project?.name || props.projectId,
	(projectName) => {
		if (projectName) {
			store.fetchMilestones(projectName);
		}
	},
	{ immediate: true }
);

function handleRefresh() {
	store.fetchTasks(props.projectId, activeFilters.value);
}

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
	const hasMilestoneFilter = store.activeMilestoneFilter.length > 0;
	let baseTasks = hasMilestoneFilter ? store.tasksFilteredByMilestone : store.tasks;

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
	// Search filter
	if (activeFilters.value.search) {
		const query = activeFilters.value.search.toLowerCase();
		result = result.filter((t) => t.subject?.toLowerCase().includes(query));
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

function formatMilestoneDate(dateStr) {
	if (!dateStr) return translate("No deadline");
	const date = new Date(dateStr);
	return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

const groupedTasksByMilestone = computed(() => {
	const groups = new Map();
	const unassignedKey = "__none__";

	store.milestones.forEach((milestone) => {
		groups.set(milestone.name, {
			key: milestone.name,
			label: milestone.milestone_name,
			meta: milestone,
			tasks: [],
			isUnassigned: false,
		});
	});

	groups.set(unassignedKey, {
		key: unassignedKey,
		label: translate("No milestone"),
		meta: null,
		tasks: [],
		isUnassigned: true,
	});

	flattenedTasksWithFilters.value.forEach((task) => {
		const groupKey = task.milestone && groups.has(task.milestone) ? task.milestone : unassignedKey;
		groups.get(groupKey).tasks.push(task);
	});

	const sorted = Array.from(groups.values()).filter((group) => group.tasks.length > 0);
	sorted.sort((a, b) => {
		if (a.isUnassigned) return 1;
		if (b.isUnassigned) return -1;
		const aDate = a.meta?.milestone_date ? new Date(a.meta.milestone_date).getTime() : Number.POSITIVE_INFINITY;
		const bDate = b.meta?.milestone_date ? new Date(b.meta.milestone_date).getTime() : Number.POSITIVE_INFINITY;
		return aDate - bDate;
	});
	return sorted;
});

// Mobile: close sidebar when switching to mobile
watch(isMobile, (mobile) => {
	if (mobile && !sidebarCollapsed.value) {
		sidebarCollapsed.value = true;
	}
});

function closeSidebar() {
	sidebarCollapsed.value = true;
}

// Mobile task card handlers
function handleMobileTaskUpdate(taskName, updates) {
	store.updateTask(taskName, updates);
}

function handleMobileAddSubtask(parentTaskName) {
	// Expand parent
	if (!store.expandedTasks.has(parentTaskName)) {
		store.toggleExpand(parentTaskName);
	}
	// Open task detail panel instead
	const task = store.tasks.find((t) => t.name === parentTaskName);
	if (task) {
		store.selectTask(task);
	}
}

function handleMobileTaskCreated() {
	store.fetchTasks(props.projectId, activeFilters.value);
}
</script>

<template>
	<div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
		<!-- Header -->
		<header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-20">
			<div class="px-3 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between gap-2 min-h-[48px] sm:min-h-[56px]">
					<!-- Left: Back + Project name -->
					<div class="flex items-center gap-2 min-w-0 flex-1">
						<button
							@click="goBack"
							class="p-1.5 -ml-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 flex-shrink-0"
						>
							<ArrowLeft class="w-5 h-5" />
						</button>
						<div v-if="store.project" class="min-w-0">
							<h1 class="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
								{{ store.project.project_name }}
							</h1>
						</div>
						<div v-else class="h-5 w-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
					</div>

					<!-- Right: Team (hidden on mobile) + Nav -->
					<div class="flex items-center gap-2 sm:gap-3 flex-shrink-0">
						<div class="hidden sm:block">
							<ProjectTeam :project-id="projectId" />
						</div>
						<OutlinerNav />
					</div>
				</div>
			</div>
		</header>

		<!-- Main content -->
		<div class="flex-1 flex overflow-hidden relative">
			<!-- Left sidebar: Desktop = inline, Mobile = drawer overlay -->
			<!-- Desktop sidebar -->
			<aside
				v-if="!sidebarCollapsed && !isMobile"
				class="bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 overflow-y-auto w-64 relative"
			>
				<div class="w-64">
					<MilestonePanel />
					<QuickFilters :project="store.project" @filter-change="handleFilterChange" />
				</div>
			</aside>

			<!-- Mobile sidebar drawer -->
			<Transition name="slide-drawer">
				<div
					v-if="!sidebarCollapsed && isMobile"
					class="fixed inset-0 z-30 flex"
				>
					<!-- Overlay -->
					<div class="absolute inset-0 bg-black/30" @click="closeSidebar"></div>
					<!-- Drawer -->
					<aside class="relative z-10 bg-white dark:bg-gray-800 w-72 max-w-[85vw] overflow-y-auto shadow-xl">
						<div class="sticky top-0 z-10 flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
							<span class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ translate("Filters") }}</span>
							<button
								@click="closeSidebar"
								class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
							>
								<X class="w-4 h-4" />
							</button>
						</div>
						<MilestonePanel />
						<QuickFilters :project="store.project" @filter-change="handleFilterChange" />
					</aside>
				</div>
			</Transition>

			<!-- Center: Task list -->
			<main class="flex-1 overflow-y-auto">
				<!-- Project Information Panel -->
				<ProjectInfoPanel
					v-if="store.project && !store.loading"
					:project="store.project"
				/>

				<!-- Toolbar -->
				<div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-[49px] sm:top-[57px] z-10">
					<div class="px-3 sm:px-6 lg:px-8 py-2">
						<div class="flex items-center gap-2">
							<!-- Search -->
							<div class="relative flex-1">
								<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
								<input
									v-model="searchInput"
									type="text"
									:placeholder="translate('Search tasks...')"
									class="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
								/>
								<button
									v-if="searchInput"
									@click="searchInput = ''; activeFilters.search = ''; store.fetchTasks(projectId, activeFilters)"
									class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
								>
									<X class="w-4 h-4" />
								</button>
							</div>

							<!-- Filter toggle -->
							<button
								@click="sidebarCollapsed = !sidebarCollapsed"
								:class="[
									'flex items-center gap-1.5 px-2.5 sm:px-3 py-2 text-sm rounded-lg border transition-colors flex-shrink-0',
									!sidebarCollapsed || hasActiveFilters
										? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-300'
										: 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
								]"
							>
								<Filter class="w-4 h-4" />
								<span class="hidden sm:inline">{{ translate("Filters") }}</span>
								<span
									v-if="hasActiveFilters"
									class="w-2 h-2 rounded-full bg-blue-600"
								></span>
							</button>

							<!-- Refresh -->
							<button
								@click="handleRefresh"
								:disabled="store.loading"
								class="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 flex-shrink-0"
								:title="translate('Refresh')"
							>
								<RefreshCw :class="['w-4 h-4', store.loading && 'animate-spin']" />
							</button>

							<!-- View tabs -->
							<div class="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5 ml-auto">
								<button
									@click="activeView = 'list'"
									:class="[
										'flex items-center gap-1 px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors',
										activeView === 'list'
											? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
											: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100',
									]"
								>
									<LayoutList class="w-4 h-4" />
									<span class="hidden sm:inline">{{ translate("List") }}</span>
								</button>
								<button
									@click="activeView = 'board'"
									:class="[
										'flex items-center gap-1 px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors',
										activeView === 'board'
											? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
											: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100',
									]"
								>
									<Columns class="w-4 h-4" />
									<span class="hidden sm:inline">{{ translate("Board") }}</span>
								</button>
								<button
									@click="activeView = 'timeline'"
									:class="[
										'flex items-center gap-1 px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors',
										activeView === 'timeline'
											? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
											: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100',
									]"
								>
									<GanttChart class="w-4 h-4" />
									<span class="hidden sm:inline">Timeline</span>
								</button>
							</div>
						</div>
					</div>
				</div>

				<div v-if="store.loading" class="flex items-center justify-center py-12">
					<div
						class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
					></div>
				</div>

				<div v-else-if="activeView === 'list'">
					<div class="px-3 sm:px-6 lg:px-8 py-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
						<div class="inline-flex items-center rounded-lg border border-gray-200 dark:border-gray-700 p-0.5">
							<button
								@click="listMode = 'flat'"
								:class="[
									'px-2.5 py-1.5 text-xs rounded-md flex items-center gap-1.5',
									listMode === 'flat'
										? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
										: 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
								]"
							>
								<LayoutList class="w-3.5 h-3.5" />
								{{ translate("Classic list") }}
							</button>
							<button
								@click="listMode = 'milestone'"
								:class="[
									'px-2.5 py-1.5 text-xs rounded-md flex items-center gap-1.5',
									listMode === 'milestone'
										? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
										: 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
								]"
							>
								<Filter class="w-3.5 h-3.5" />
								{{ translate("Group by milestones") }}
							</button>
						</div>
					</div>

					<!-- Desktop: TaskTree grid view -->
					<template v-if="!isMobile">
						<TaskTree
							v-if="listMode === 'flat'"
							:tasks="flattenedTasksWithFilters"
							:project-id="projectId"
						/>

						<div v-else class="space-y-4 p-4 sm:p-6">
							<section
								v-for="group in groupedTasksByMilestone"
								:key="group.key"
								class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden bg-white dark:bg-gray-800"
							>
								<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80">
									<div class="flex items-center justify-between gap-2">
										<div class="min-w-0">
											<div class="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
												{{ group.label }}
											</div>
											<div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
												<span>{{ group.tasks.length }} {{ translate("tasks") }}</span>
												<span v-if="group.meta" class="ml-2">
													{{ formatMilestoneDate(group.meta.milestone_date) }}
												</span>
											</div>
										</div>
										<div
											v-if="group.meta"
											class="text-xs px-2 py-1 rounded-full border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300"
										>
											{{ group.meta.completed_tasks || 0 }}/{{ group.meta.total_tasks || 0 }}
										</div>
									</div>
								</div>
								<TaskTree
									:tasks="group.tasks"
									:project-id="projectId"
									:show-header="false"
									:show-quick-add="false"
									:enable-reorder="false"
								/>
							</section>
						</div>
					</template>

					<!-- Mobile: Card view -->
					<template v-else>
						<div v-if="listMode === 'flat'" class="p-3 space-y-2">
							<ProjectTaskCardMobile
								v-for="task in flattenedTasksWithFilters"
								:key="task.name"
								:task="task"
								:level="task.level || 0"
								@click="handleTaskClick"
								@update="handleMobileTaskUpdate"
								@add-subtask="handleMobileAddSubtask"
							/>
							<!-- Quick add task -->
							<div class="mt-2">
								<QuickAddTask
									:project-id="projectId"
									:parent-task="null"
									:placeholder="translate('Add a task...')"
									@created="handleMobileTaskCreated"
								/>
							</div>
						</div>

						<div v-else class="p-3 space-y-3">
							<section
								v-for="group in groupedTasksByMilestone"
								:key="group.key"
								class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden bg-white dark:bg-gray-800"
							>
								<div class="px-3 py-2.5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80">
									<div class="flex items-center justify-between gap-2">
										<div class="min-w-0">
											<div class="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
												{{ group.label }}
											</div>
											<div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
												<span>{{ group.tasks.length }} {{ translate("tasks") }}</span>
												<span v-if="group.meta" class="ml-2">
													{{ formatMilestoneDate(group.meta.milestone_date) }}
												</span>
											</div>
										</div>
										<div
											v-if="group.meta"
											class="text-xs px-2 py-1 rounded-full border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300"
										>
											{{ group.meta.completed_tasks || 0 }}/{{ group.meta.total_tasks || 0 }}
										</div>
									</div>
								</div>
								<div class="p-2 space-y-2">
									<ProjectTaskCardMobile
										v-for="task in group.tasks"
										:key="task.name"
										:task="task"
										:level="task.level || 0"
										@click="handleTaskClick"
										@update="handleMobileTaskUpdate"
										@add-subtask="handleMobileAddSubtask"
									/>
								</div>
							</section>
						</div>
					</template>
				</div>

				<div v-else-if="activeView === 'board'" class="h-full">
					<KanbanBoard
						:tasks="flattenedTasksWithFilters"
						:project-id="projectId"
						:is-mobile="isMobile"
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

		<BackToDeskButton />
	</div>
</template>

<style scoped>
.slide-drawer-enter-active,
.slide-drawer-leave-active {
	transition: opacity 0.25s ease;
}
.slide-drawer-enter-active aside,
.slide-drawer-leave-active aside {
	transition: transform 0.25s ease;
}
.slide-drawer-enter-from,
.slide-drawer-leave-to {
	opacity: 0;
}
.slide-drawer-enter-from aside,
.slide-drawer-leave-to aside {
	transform: translateX(-100%);
}
</style>
