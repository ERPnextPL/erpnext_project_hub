<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useDebounceFn, useWindowSize } from "@vueuse/core";
import { useTaskStore } from "../stores/taskStore";
import TaskTree from "../components/TaskTree.vue";
import ProjectTaskCardMobile from "../components/ProjectTaskCardMobile.vue";
import TaskDetailPanel from "../components/TaskDetailPanel.vue";
import QuickFilters from "../components/QuickFilters.vue";
import ProjectTeam from "../components/ProjectTeam.vue";
import MilestoneSidebar from "../components/MilestoneSidebar.vue";
import ProjectInfoPanel from "../components/ProjectInfoPanel.vue";
import ProjectAttachmentsSidebar from "../components/ProjectAttachmentsSidebar.vue";
import ProjectManagerPanel from "../components/ProjectManagerPanel.vue";
import KanbanBoard from "../components/KanbanBoard.vue";
import TimelineView from "../components/TimelineView.vue";
import {
	ArrowLeft,
	Filter,
	Search,
	X,
	RefreshCw,
	LayoutList,
	Columns,
	GanttChart,
	Paperclip,
	Diamond,
	GripVertical,
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

const activeView = ref("list");
const listMode = ref("milestone");
const sidebarCollapsed = ref(true); // Domyślnie zwinięty
const milestoneSidebarOpen = ref(false);
const attachmentsSidebarOpen = ref(false);
const attachmentCount = ref(0);
const searchInput = ref("");
const { width } = useWindowSize();
const isMobile = computed(() => width.value < 1024);
const draggingGroupKey = ref(null);
const groupReorderDropIndex = ref(null);
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

watch(isMobile, (mobile) => {
	if (mobile) {
		milestoneSidebarOpen.value = false;
		attachmentsSidebarOpen.value = false;
	}
});

function handleEscape(event) {
	if (event.key === "Escape") {
		milestoneSidebarOpen.value = false;
		attachmentsSidebarOpen.value = false;
	}
}

onMounted(() => {
	window.addEventListener("keydown", handleEscape);
});

onUnmounted(() => {
	window.removeEventListener("keydown", handleEscape);
});

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

function closeAttachmentsSidebar() {
	attachmentsSidebarOpen.value = false;
}

function closeMilestoneSidebar() {
	milestoneSidebarOpen.value = false;
}

function handleAttachmentsUpdated(count) {
	attachmentCount.value = count;
}

// Helper to get today's date in YYYY-MM-DD format
function getTodayDate() {
	const today = new Date();
	return today.toISOString().split("T")[0];
}

function formatMilestoneDate(dateStr) {
	if (!dateStr) return translate("No deadline");
	const date = new Date(dateStr);
	return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function handleGroupDragStart(event, groupKey) {
	draggingGroupKey.value = groupKey;
	event.dataTransfer.setData("application/x-milestone-reorder", groupKey);
	event.dataTransfer.setData("text/plain", "");
	event.dataTransfer.effectAllowed = "move";
}

function handleGroupDragEnd() {
	draggingGroupKey.value = null;
	groupReorderDropIndex.value = null;
}

function handleGroupDragOver(event, index) {
	if (!draggingGroupKey.value && !event.dataTransfer.types.includes("application/x-milestone-reorder")) {
		return;
	}
	event.preventDefault();
	event.dataTransfer.dropEffect = "move";
	groupReorderDropIndex.value = index;
}

function handleGroupDragLeave(event) {
	if (event.currentTarget.contains(event.relatedTarget)) return;
	groupReorderDropIndex.value = null;
}

async function handleGroupDrop(event, index) {
	event.preventDefault();

	const draggedKey =
		draggingGroupKey.value || event.dataTransfer.getData("application/x-milestone-reorder");

	draggingGroupKey.value = null;
	groupReorderDropIndex.value = null;

	if (!draggedKey) return;

	const groups = [...groupedTasksByMilestone.value];
	const fromIndex = groups.findIndex((group) => group.key === draggedKey);

	if (fromIndex === -1 || fromIndex === index) return;

	const [movedGroup] = groups.splice(fromIndex, 1);
	groups.splice(index, 0, movedGroup);

	try {
		// Use store.milestones to include ALL milestones (including empty/hidden ones)
		// groupedTasksByMilestone only contains milestones with tasks, so empty milestones would be omitted
		const allMilestoneKeys = store.milestones.map((m) => m.name);
		const reorderedKeys = groups
			.filter((group) => !group.isUnassigned)
			.map((group) => group.key);

		// Build final order: start with all milestones in original order,
		// then apply the new order for milestones that have tasks
		const finalKeys = [...allMilestoneKeys];
		let reorderedIdx = 0;
		for (let i = 0; i < finalKeys.length; i++) {
			const key = finalKeys[i];
			if (reorderedKeys.includes(key)) {
				finalKeys[i] = reorderedKeys[reorderedIdx++];
			}
		}

		await store.reorderMilestones(finalKeys);
	} catch (error) {
		window.frappe?.show_alert({
			message: translate("Failed to reorder milestones"),
			indicator: "red",
		});
	}
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

const groupedTasksByMilestone = computed(() => {
	const groups = [];
	const tasksByMilestone = new Map();
	const unassignedTasks = [];

	for (const milestone of store.milestones) {
		tasksByMilestone.set(milestone.name, []);
	}

	for (const task of flattenedTasksWithFilters.value) {
		if (task.milestone && tasksByMilestone.has(task.milestone)) {
			tasksByMilestone.get(task.milestone).push(task);
		} else {
			unassignedTasks.push(task);
		}
	}

	for (const milestone of store.milestones) {
		const tasks = tasksByMilestone.get(milestone.name) || [];
		if (tasks.length > 0) {
			groups.push({
				key: milestone.name,
				label: milestone.milestone_name || milestone.name,
				meta: milestone,
				tasks,
				isUnassigned: false,
			});
		}
	}

	if (unassignedTasks.length > 0) {
		groups.push({
			key: "__none__",
			label: translate("No milestone"),
			meta: null,
			tasks: unassignedTasks,
			isUnassigned: true,
		});
	}

	const mode = store.milestoneSortBy || "manual";

	groups.sort((a, b) => {
		if (a.isUnassigned) return 1;
		if (b.isUnassigned) return -1;

		if (mode === "name") {
			return (a.label || "").localeCompare(b.label || "");
		}

		if (mode === "progress") {
			return (b.meta?.progress || 0) - (a.meta?.progress || 0);
		}

		if (mode === "deadline") {
			const aDate = a.meta?.milestone_date
				? new Date(a.meta.milestone_date).getTime()
				: Number.POSITIVE_INFINITY;
			const bDate = b.meta?.milestone_date
				? new Date(b.meta.milestone_date).getTime()
				: Number.POSITIVE_INFINITY;
			return aDate - bDate;
		}

		return (a.meta?.sort_order || 0) - (b.meta?.sort_order || 0);
	});

	return groups;
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

					<!-- Right: Team + Nav -->
					<div class="flex items-center gap-3 flex-wrap justify-end">
						<ProjectTeam :project-id="projectId" />
						<button
							@click="attachmentsSidebarOpen = !attachmentsSidebarOpen"
							:class="[
								'flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors',
								attachmentsSidebarOpen
									? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300'
									: 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
							]"
							:title="translate('Attachments')"
						>
							<Paperclip class="w-4 h-4" />
							<span class="hidden sm:inline">{{ translate("Attachments") }}</span>
							<span
								v-if="attachmentCount > 0"
								class="ml-1 rounded-full bg-emerald-600 px-1.5 py-0.5 text-[10px] font-semibold text-white"
							>
								{{ attachmentCount }}
							</span>
						</button>
						<OutlinerNav />
					</div>
					</div>
			</div>
		</header>

			<!-- Main content -->
			<div class="flex-1 flex overflow-hidden relative">
				<Transition name="fade">
					<div
						v-if="milestoneSidebarOpen && isMobile"
						class="absolute inset-0 z-20 bg-black/20"
						@click="closeMilestoneSidebar"
					></div>
				</Transition>

				<Transition name="slide-sidebar-left">
					<div
						v-if="milestoneSidebarOpen"
						:class="[
							'z-30 flex-shrink-0 overflow-y-auto',
							isMobile ? 'absolute inset-y-0 left-0' : 'relative',
						]"
					>
						<MilestoneSidebar @close="closeMilestoneSidebar" />
					</div>
				</Transition>

				<Transition name="slide-sidebar-right">
					<div
						v-if="attachmentsSidebarOpen"
						class="order-last flex-shrink-0 overflow-y-auto relative"
					>
						<ProjectAttachmentsSidebar
							:project-id="projectId"
							:project="store.project"
							@close="closeAttachmentsSidebar"
							@updated="handleAttachmentsUpdated"
						/>
					</div>
				</Transition>

				<!-- Left sidebar: Milestones + Filters (collapsible) -->
			<aside
				v-if="!sidebarCollapsed"
				class="bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 overflow-y-auto w-64 relative"
			>
				<div class="w-64">
					<!-- Quick Filters -->
					<QuickFilters :project="store.project" @filter-change="handleFilterChange" />
				</div>
			</aside>

			<!-- Center: Task list -->
			<main class="flex-1 overflow-y-auto">
				<!-- Project Information Panel -->
				<ProjectInfoPanel
					v-if="store.project && !store.loading"
					:project="store.project"
				/>
				<ProjectManagerPanel
					v-if="store.project && !store.loading && store.project.is_manager"
					:project="store.project"
				/>

				<!-- Toolbar: View tabs + Search + Filter + Refresh -->
				<div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-[57px] z-10">
					<div class="px-4 sm:px-6 lg:px-8 py-2">
						<div class="flex flex-col sm:flex-row sm:items-center gap-3">
							<!-- Search -->
							<div class="relative flex-1 max-w-md">
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

							<!-- Filter toggle + Refresh -->
							<div class="flex items-center gap-2">
								<button
									@click="milestoneSidebarOpen = !milestoneSidebarOpen"
									:class="[
										'flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors',
										milestoneSidebarOpen
											? 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300'
											: 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
									]"
									:title="translate('Milestones')"
								>
									<Diamond class="w-4 h-4" />
									<span
										v-if="store.milestones.length"
										class="rounded-full bg-purple-600 px-1.5 py-0.5 text-[10px] font-semibold text-white"
									>
										{{ store.milestones.length }}
									</span>
								</button>

								<button
									@click="sidebarCollapsed = !sidebarCollapsed"
									:class="[
										'flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors',
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

								<button
									@click="handleRefresh"
									:disabled="store.loading"
									class="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
									:title="translate('Refresh')"
								>
									<RefreshCw :class="['w-4 h-4', store.loading && 'animate-spin']" />
								</button>
							</div>

							<!-- View tabs (right-aligned) -->
							<div class="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5 sm:ml-auto">
								<button
									@click="activeView = 'list'"
									:class="[
										'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
										activeView === 'list'
											? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
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
											? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
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
											? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
											: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100',
									]"
								>
									<GanttChart class="w-4 h-4" />
									{{ translate("Timeline") }}
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
					<div class="border-b border-gray-200 bg-white px-4 py-2 dark:border-gray-700 dark:bg-gray-800 sm:px-6 lg:px-8">
						<div class="flex flex-wrap items-center gap-3">
							<div class="inline-flex items-center rounded-lg border border-gray-200 p-0.5 dark:border-gray-700">
							<button
								@click="listMode = 'flat'"
								:class="[
									'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs',
									listMode === 'flat'
										? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
										: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700',
								]"
							>
								<LayoutList class="h-3.5 w-3.5" />
								{{ translate("Classic list") }}
							</button>
							<button
								@click="listMode = 'milestone'"
								:class="[
									'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs',
									listMode === 'milestone'
										? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
										: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700',
								]"
							>
								<Diamond class="h-3.5 w-3.5" />
								{{ translate("Group by milestones") }}
							</button>
							</div>
							<div
								v-if="listMode === 'milestone'"
								class="inline-flex items-center rounded-lg border border-gray-200 p-0.5 text-xs dark:border-gray-700"
							>
								<button
									@click="store.milestoneSortBy = 'manual'"
									:class="[
										'rounded-md px-2.5 py-1.5',
										store.milestoneSortBy === 'manual'
											? 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
											: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700',
									]"
								>
									{{ translate("Manual") }}
								</button>
								<button
									@click="store.milestoneSortBy = 'deadline'"
									:class="[
										'rounded-md px-2.5 py-1.5',
										store.milestoneSortBy === 'deadline'
											? 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
											: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700',
									]"
								>
									{{ translate("Deadline") }}
								</button>
								<button
									@click="store.milestoneSortBy = 'name'"
									:class="[
										'rounded-md px-2.5 py-1.5',
										store.milestoneSortBy === 'name'
											? 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
											: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700',
									]"
								>
									{{ translate("Name") }}
								</button>
								<button
									@click="store.milestoneSortBy = 'progress'"
									:class="[
										'rounded-md px-2.5 py-1.5',
										store.milestoneSortBy === 'progress'
											? 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
											: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700',
									]"
								>
									{{ translate("Progress") }}
								</button>
							</div>
						</div>
					</div>

					<TaskTree
						v-if="listMode === 'flat'"
						:tasks="flattenedTasksWithFilters"
						:project-id="projectId"
					/>

					<div v-else-if="!isMobile" class="space-y-4 p-4 sm:p-6">
						<div class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
							<TaskTree
								:tasks="[]"
								:project-id="projectId"
								:show-quick-add="false"
								:enable-reorder="false"
								:show-body="false"
							/>
						</div>

						<section
							v-for="(group, index) in groupedTasksByMilestone"
							:key="group.key"
							:draggable="store.milestoneSortBy === 'manual' && !group.isUnassigned"
							@dragstart="store.milestoneSortBy === 'manual' && !group.isUnassigned && handleGroupDragStart($event, group.key)"
							@dragend="handleGroupDragEnd"
							@dragover="handleGroupDragOver($event, index)"
							@dragleave="handleGroupDragLeave"
							@drop="handleGroupDrop($event, index)"
							:class="[
								'overflow-hidden rounded-xl border bg-white dark:bg-gray-800',
								draggingGroupKey === group.key
									? 'opacity-40 border-gray-200 dark:border-gray-700'
									: groupReorderDropIndex === index && draggingGroupKey !== group.key
										? 'border-purple-400 shadow-md dark:border-purple-500'
										: 'border-gray-200 dark:border-gray-700',
							]"
						>
							<div class="border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800/80">
								<div class="flex items-center justify-between gap-2">
									<div class="flex min-w-0 items-center gap-1.5">
										<GripVertical
											v-if="store.milestoneSortBy === 'manual' && !group.isUnassigned"
											class="h-3.5 w-3.5 flex-shrink-0 cursor-grab text-gray-300 active:cursor-grabbing dark:text-gray-600"
										/>
										<div class="min-w-0">
										<div class="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">
											{{ group.label }}
										</div>
										<div class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
											<span>{{ group.tasks.length }} {{ translate("tasks") }}</span>
											<span v-if="group.meta" class="ml-2">
												{{ formatMilestoneDate(group.meta.milestone_date) }}
											</span>
										</div>
										</div>
									</div>
									<div
										v-if="group.meta"
										class="rounded-full border border-gray-200 px-2 py-1 text-xs text-gray-600 dark:border-gray-600 dark:text-gray-300"
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

					<div v-else class="space-y-3 p-3">
						<section
							v-for="group in groupedTasksByMilestone"
							:key="group.key"
							class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
						>
							<div class="border-b border-gray-200 bg-gray-50 px-3 py-2.5 dark:border-gray-700 dark:bg-gray-800/80">
								<div class="flex items-center justify-between gap-2">
									<div class="min-w-0">
										<div class="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">
											{{ group.label }}
										</div>
										<div class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
											<span>{{ group.tasks.length }} {{ translate("tasks") }}</span>
											<span v-if="group.meta" class="ml-2">
												{{ formatMilestoneDate(group.meta.milestone_date) }}
											</span>
										</div>
									</div>
									<div
										v-if="group.meta"
										class="rounded-full border border-gray-200 px-2 py-1 text-[11px] text-gray-600 dark:border-gray-600 dark:text-gray-300"
									>
										{{ group.meta.completed_tasks || 0 }}/{{ group.meta.total_tasks || 0 }}
									</div>
								</div>
							</div>
							<div class="space-y-2 p-2">
								<ProjectTaskCardMobile
									v-for="task in group.tasks"
									:key="task.name"
									:task="task"
									:level="task.level || 0"
									@click="handleTaskClick"
								/>
							</div>
						</section>
					</div>
				</div>

				<div v-else-if="activeView === 'board'" class="h-full">
					<KanbanBoard
						:tasks="flattenedTasksWithFilters"
						:project-id="projectId"
						:visible-statuses="activeFilters.status"
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
