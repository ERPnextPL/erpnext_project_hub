<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import {
	Folder,
	Archive,
	PauseCircle,
	ChevronDown,
	LayoutGrid,
	List,
	Search,
	ArrowUpDown,
	ArrowUp,
	ArrowDown,
	X,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import BackToDeskButton from "../components/BackToDeskButton.vue";
import ProjectCard from "../components/ProjectCard.vue";
import ProjectListRow from "../components/ProjectListRow.vue";
import ProjectListHeader from "../components/ProjectListHeader.vue";
import { translate } from "../utils/translation";

const router = useRouter();
const activeProjects = ref([]);
const onHoldProjects = ref([]);
const completedProjects = ref([]);
const isManager = ref(false);
const loading = ref(true);
const showCompleted = ref(false);
const showOnHold = ref(false);

// View mode: 'grid' | 'list'
const viewMode = ref("grid");

// Search
const searchQuery = ref("");

// Sort: field + direction
const sortField = ref(null); // null = default (server order)
const sortDir = ref("asc");

const SORT_OPTIONS = [
	{ value: "project_name", label: translate("Name") },
	{ value: "percent_complete", label: translate("Progress") },
	{ value: "expected_end_date", label: translate("Deadline") },
	{ value: "task_count", label: translate("Tasks") },
];

onMounted(async () => {
	try {
		const response = await fetch(
			"/api/method/erpnext_projekt_hub.api.project_hub.get_projects",
			{
				headers: { "X-Frappe-CSRF-Token": window.csrf_token },
			}
		);
		const data = await response.json();
		const result = data.message || { active: [], on_hold: [], completed: [], is_manager: false };
		activeProjects.value = result.active || [];
		onHoldProjects.value = result.on_hold || [];
		completedProjects.value = result.completed || [];
		isManager.value = result.is_manager || false;
	} catch (error) {
		console.error("Failed to fetch projects:", error);
	} finally {
		loading.value = false;
	}
});

function applySearchAndSort(projects) {
	let list = projects;

	if (searchQuery.value.trim()) {
		const q = searchQuery.value.trim().toLowerCase();
		list = list.filter((p) => p.project_name?.toLowerCase().includes(q));
	}

	if (sortField.value) {
		list = [...list].sort((a, b) => {
			let av = a[sortField.value];
			let bv = b[sortField.value];

			if (sortField.value === "expected_end_date") {
				av = av ? new Date(av).getTime() : Infinity;
				bv = bv ? new Date(bv).getTime() : Infinity;
			} else if (typeof av === "string" || typeof bv === "string" || av == null || bv == null) {
				av = (av ?? "").toString().toLowerCase();
				bv = (bv ?? "").toString().toLowerCase();
			} else {
				av = av ?? -Infinity;
				bv = bv ?? -Infinity;
			}

			if (av < bv) return sortDir.value === "asc" ? -1 : 1;
			if (av > bv) return sortDir.value === "asc" ? 1 : -1;
			return 0;
		});
	}

	return list;
}

const filteredActiveProjects = computed(() => applySearchAndSort(activeProjects.value));
const filteredOnHoldProjects = computed(() => applySearchAndSort(onHoldProjects.value));
const filteredCompletedProjects = computed(() => applySearchAndSort(completedProjects.value));

const hasProjects = computed(
	() =>
		activeProjects.value.length > 0 ||
		onHoldProjects.value.length > 0 ||
		completedProjects.value.length > 0
);

const hasResults = computed(
	() =>
		filteredActiveProjects.value.length > 0 ||
		filteredOnHoldProjects.value.length > 0 ||
		filteredCompletedProjects.value.length > 0
);

function openProject(projectId) {
	router.push({ name: "ProjectOutliner", params: { projectId } });
}

function toggleSort(field) {
	if (sortField.value === field) {
		sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
	} else {
		sortField.value = field;
		sortDir.value = "asc";
	}
}

function clearSort() {
	sortField.value = null;
	sortDir.value = "asc";
}

function sortIcon(field) {
	if (sortField.value !== field) return ArrowUpDown;
	return sortDir.value === "asc" ? ArrowUp : ArrowDown;
}
</script>

<template>
	<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
		<!-- Header -->
		<header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-20">
			<div class="w-full px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<Folder class="w-6 h-6 text-blue-600" />
						<h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
							{{ translate("Projects") }}
						</h1>
					</div>
					<div class="flex items-center gap-3 sm:gap-4">
						<OutlinerNav />
					</div>
				</div>
			</div>
		</header>

		<!-- Content -->
		<main class="w-full px-4 sm:px-6 lg:px-8 py-8">
			<!-- Top bar: title + counters + view toggle -->
			<div class="mb-4 flex flex-wrap items-center justify-between gap-3">
				<div>
					<h2 class="text-lg font-medium text-gray-900 dark:text-gray-100">
						{{ isManager ? translate("All projects") : translate("My projects") }}
					</h2>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{{
							isManager
								? translate("Manage all projects")
								: translate("Projects with assigned tasks")
						}}
					</p>
				</div>
				<div class="flex items-center gap-2">
					<span class="px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm rounded-md">
						{{ activeProjects.length }} {{ translate("active") }}
					</span>
					<span
						v-if="onHoldProjects.length > 0"
						class="px-2 py-1 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-sm rounded-md"
					>
						{{ onHoldProjects.length }} {{ translate("on hold") }}
					</span>
					<span
						v-if="completedProjects.length > 0"
						class="px-2 py-1 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm rounded-md"
					>
						{{ completedProjects.length }} {{ translate("completed") }}
					</span>
					<!-- View toggle -->
					<div class="flex items-center border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden ml-2">
						<button
							@click="viewMode = 'grid'"
							:class="[
								'p-2 transition-colors',
								viewMode === 'grid'
									? 'bg-blue-600 text-white'
									: 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700',
							]"
							:title="translate('Grid view')"
						>
							<LayoutGrid class="w-4 h-4" />
						</button>
						<button
							@click="viewMode = 'list'"
							:class="[
								'p-2 transition-colors',
								viewMode === 'list'
									? 'bg-blue-600 text-white'
									: 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700',
							]"
							:title="translate('List view')"
						>
							<List class="w-4 h-4" />
						</button>
					</div>
				</div>
			</div>

			<!-- Search + Sort bar -->
			<div class="mb-6 flex flex-wrap items-center gap-3">
				<!-- Search -->
				<div class="relative flex-1 min-w-[200px] max-w-sm">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
					<input
						v-model="searchQuery"
						type="text"
						:placeholder="translate('Search projects...')"
						class="w-full pl-9 pr-8 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
					/>
					<button
						v-if="searchQuery"
						@click="searchQuery = ''"
						class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
					>
						<X class="w-3.5 h-3.5" />
					</button>
				</div>

				<!-- Sort buttons (list view) / Sort dropdown area -->
				<div class="flex items-center gap-2 flex-wrap">
					<span class="text-xs text-gray-500 dark:text-gray-400">{{ translate("Sort by") }}:</span>
					<div class="flex items-center gap-1">
						<button
							v-for="opt in SORT_OPTIONS"
							:key="opt.value"
							@click="toggleSort(opt.value)"
							:class="[
								'flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-md border transition-colors',
								sortField === opt.value
									? 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-600 text-blue-700 dark:text-blue-300'
									: 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
							]"
						>
							{{ opt.label }}
							<component :is="sortIcon(opt.value)" class="w-3 h-3" />
						</button>
						<button
							v-if="sortField"
							@click="clearSort"
							class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
							:title="translate('Clear sort')"
						>
							<X class="w-3.5 h-3.5" />
						</button>
					</div>
				</div>
			</div>

			<!-- Loading -->
			<div v-if="loading" class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			</div>

			<!-- Empty state (no projects at all) -->
			<div
				v-else-if="!hasProjects"
				class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
			>
				<Folder class="w-12 h-12 text-gray-400 mx-auto mb-4" />
				<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
					{{ translate("No projects found") }}
				</h3>
				<p class="text-gray-500 dark:text-gray-400">
					{{
						isManager
							? translate("Create a project in ERPNext to get started.")
							: translate("You don't have any tasks assigned to projects yet.")
					}}
				</p>
			</div>

			<!-- No search results -->
			<div
				v-else-if="!hasResults"
				class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
			>
				<Search class="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
				<p class="text-gray-500 dark:text-gray-400">
					{{ translate("No projects match") }} „{{ searchQuery }}"
				</p>
				<button
					@click="searchQuery = ''"
					class="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
				>
					{{ translate("Clear search") }}
				</button>
			</div>

			<div v-else>
				<!-- ─── ACTIVE PROJECTS ─────────────────────────────────── -->
				<section v-if="filteredActiveProjects.length > 0" class="mb-8">
					<h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
						<Folder class="w-4 h-4" />
						{{ translate("Active projects") }} ({{ filteredActiveProjects.length }})
					</h3>

					<div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						<ProjectCard
							v-for="project in filteredActiveProjects"
							:key="project.name"
							:project="project"
							variant="active"
							@open="openProject"
						/>
					</div>
					<div v-else class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
						<ProjectListHeader sortable :sort-icon="sortIcon" :toggle-sort="toggleSort" />
						<ProjectListRow
							v-for="project in filteredActiveProjects"
							:key="project.name"
							:project="project"
							variant="active"
							@open="openProject"
						/>
					</div>
				</section>

				<!-- ─── ON HOLD PROJECTS ────────────────────────────────── -->
				<section v-if="onHoldProjects.length > 0" class="mb-8">
					<button
						@click="showOnHold = !showOnHold"
						class="w-full flex items-center justify-between py-3 px-4 bg-amber-50 dark:bg-amber-900/20 hover:bg-amber-100 dark:hover:bg-amber-900/30 rounded-lg transition-colors mb-4"
					>
						<div class="flex items-center gap-2 text-sm font-semibold text-amber-700 dark:text-amber-300">
							<PauseCircle class="w-4 h-4" />
							<span>{{ translate("On hold projects") }} ({{ filteredOnHoldProjects.length }})</span>
						</div>
						<div class="flex items-center gap-2 text-amber-600 dark:text-amber-400">
							<span class="text-xs">{{ showOnHold ? translate("Hide") : translate("Show") }}</span>
							<ChevronDown class="w-4 h-4 transition-transform duration-200" :class="showOnHold ? 'rotate-180' : ''" />
						</div>
					</button>

					<Transition name="slide-fade">
						<div v-if="showOnHold">
							<div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
								<ProjectCard
									v-for="project in filteredOnHoldProjects"
									:key="project.name"
									:project="project"
									variant="onHold"
									@open="openProject"
								/>
							</div>
							<div v-else class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
								<ProjectListHeader />
								<ProjectListRow
									v-for="project in filteredOnHoldProjects"
									:key="project.name"
									:project="project"
									variant="onHold"
									@open="openProject"
								/>
							</div>
						</div>
					</Transition>
				</section>

				<!-- ─── COMPLETED PROJECTS ─────────────────────────────── -->
				<section v-if="completedProjects.length > 0">
					<button
						@click="showCompleted = !showCompleted"
						class="w-full flex items-center justify-between py-3 px-4 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors mb-4"
					>
						<div class="flex items-center gap-2 text-sm font-semibold text-gray-600 dark:text-gray-300">
							<Archive class="w-4 h-4" />
							<span>{{ translate("Completed projects") }} ({{ filteredCompletedProjects.length }})</span>
						</div>
						<div class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
							<span class="text-xs">{{ showCompleted ? translate("Hide") : translate("Show") }}</span>
							<ChevronDown class="w-4 h-4 transition-transform duration-200" :class="showCompleted ? 'rotate-180' : ''" />
						</div>
					</button>

					<Transition name="slide-fade">
						<div v-if="showCompleted">
							<div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
								<ProjectCard
									v-for="project in filteredCompletedProjects"
									:key="project.name"
									:project="project"
									variant="completed"
									@open="openProject"
								/>
							</div>
							<div v-else class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
								<ProjectListHeader />
								<ProjectListRow
									v-for="project in filteredCompletedProjects"
									:key="project.name"
									:project="project"
									variant="completed"
									@open="openProject"
								/>
							</div>
						</div>
					</Transition>
				</section>
			</div>
		</main>

		<BackToDeskButton />
	</div>
</template>

<style scoped>
.slide-fade-enter-active {
	transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
	transition: all 0.2s ease-in;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
	opacity: 0;
	transform: translateY(-10px);
}
</style>
