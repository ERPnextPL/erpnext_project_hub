<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import {
	Folder,
	ChevronRight,
	Calendar,
	Users,
	CheckCircle2,
	Archive,
	ChevronDown,
	Flag,
	LayoutGrid,
	List,
	Search,
	ArrowUpDown,
	ArrowUp,
	ArrowDown,
	User,
	X,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import BackToDeskButton from "../components/BackToDeskButton.vue";
import { translate } from "../utils/translation";
import { getProgressColorClass } from "../utils/progressColors";

const router = useRouter();
const activeProjects = ref([]);
const completedProjects = ref([]);
const isManager = ref(false);
const loading = ref(true);
const showCompleted = ref(false);

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
		const result = data.message || { active: [], completed: [], is_manager: false };
		activeProjects.value = result.active || [];
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
			} else if (typeof av === "string") {
				av = av?.toLowerCase() ?? "";
				bv = bv?.toLowerCase() ?? "";
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
const filteredCompletedProjects = computed(() => applySearchAndSort(completedProjects.value));

const hasProjects = computed(
	() => activeProjects.value.length > 0 || completedProjects.value.length > 0
);

const hasResults = computed(
	() => filteredActiveProjects.value.length > 0 || filteredCompletedProjects.value.length > 0
);

function openProject(projectId) {
	router.push({ name: "ProjectOutliner", params: { projectId } });
}

function getStatusClass(status) {
	const classes = {
		Open: "bg-blue-100 text-blue-800",
		Completed: "bg-green-100 text-green-800",
		Cancelled: "bg-gray-100 text-gray-600",
	};
	return classes[status] || "bg-gray-100 text-gray-600";
}

function customerInitials(name) {
	if (!name) return "?";
	return name
		.split(/\s+/)
		.slice(0, 2)
		.map((w) => w[0].toUpperCase())
		.join("");
}

function formatDate(dateStr) {
	if (!dateStr) return null;
	const d = new Date(dateStr);
	return d.toLocaleDateString("pl-PL", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function isOverdue(project) {
	if (!project.expected_end_date || project.status === "Completed") return false;
	return new Date(project.expected_end_date) < new Date();
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

					<!-- GRID VIEW -->
					<div
						v-if="viewMode === 'grid'"
						class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
					>
						<div
							v-for="project in filteredActiveProjects"
							:key="project.name"
							@click="openProject(project.name)"
							class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md transition-all cursor-pointer group"
						>
							<div class="flex items-start justify-between mb-3">
								<div class="flex items-center gap-2.5 min-w-0">
									<img
										v-if="project.customer_image"
										:src="project.customer_image"
										:alt="project.customer_name"
										class="w-8 h-8 rounded-md object-contain border border-gray-100 dark:border-gray-700 bg-white flex-shrink-0"
									/>
									<div
										v-else-if="project.customer_name"
										class="w-8 h-8 rounded-md flex items-center justify-center text-xs font-semibold bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 flex-shrink-0 select-none"
									>
										{{ customerInitials(project.customer_name) }}
									</div>
									<Folder v-else class="w-5 h-5 text-blue-600 flex-shrink-0" />
									<h3 class="font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 truncate">
										{{ project.project_name }}
									</h3>
								</div>
								<ChevronRight class="w-5 h-5 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors flex-shrink-0" />
							</div>

							<!-- Progress -->
							<div class="mb-3">
								<div class="flex items-center justify-between text-xs mb-1">
									<span class="text-gray-500 dark:text-gray-400">{{ translate("Progress") }}</span>
									<span class="font-medium text-gray-700 dark:text-gray-300">{{ project.percent_complete || 0 }}%</span>
								</div>
								<div class="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
									<div
										class="h-full rounded-full transition-all duration-300"
										:class="getProgressColorClass(project.percent_complete || 0)"
										:style="{ width: (project.percent_complete || 0) + '%' }"
									></div>
								</div>
							</div>

							<div class="space-y-1.5">
								<div class="flex items-center gap-2 text-sm">
									<span :class="['px-2 py-0.5 rounded-full text-xs font-medium', getStatusClass(project.status)]">
										{{ translate(project.status) }}
									</span>
								</div>

								<div v-if="project.expected_end_date" class="flex items-center gap-1.5 text-sm" :class="isOverdue(project) ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'">
									<Calendar class="w-3.5 h-3.5" />
									<span>{{ formatDate(project.expected_end_date) }}</span>
									<span v-if="isOverdue(project)" class="text-xs font-medium">({{ translate("overdue") }})</span>
								</div>

								<div v-if="project.project_manager_name" class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
									<User class="w-3.5 h-3.5" />
									<span class="truncate">{{ project.project_manager_name }}</span>
								</div>

								<div class="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
									<div class="flex items-center gap-1.5">
										<Users class="w-3.5 h-3.5" />
										<span>{{ project.task_count || 0 }} {{ translate("tasks") }}</span>
									</div>
									<div v-if="project.user_task_count" class="flex items-center gap-1 text-blue-600 dark:text-blue-400">
										<span>{{ project.user_task_count }} {{ translate("yours") }}</span>
									</div>
								</div>

								<div v-if="project.assigned_users_count > 0" class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
									<Users class="w-3.5 h-3.5 text-purple-500" />
									<span>{{ project.assigned_users_count }} {{ project.assigned_users_count === 1 ? translate("person") : translate("people") }}</span>
								</div>

								<div v-if="project.next_milestone" class="flex items-center gap-1.5 text-sm">
									<Flag class="w-3.5 h-3.5 text-amber-500" />
									<span :class="[project.days_to_milestone < 0 ? 'text-red-600 dark:text-red-400 font-medium' : project.days_to_milestone <= 3 ? 'text-amber-600 dark:text-amber-400 font-medium' : 'text-gray-500 dark:text-gray-400']">
										<template v-if="project.days_to_milestone < 0">{{ translate("Milestone overdue") }}</template>
										<template v-else-if="project.days_to_milestone === 0">{{ translate("Milestone due today") }}</template>
										<template v-else-if="project.days_to_milestone === 1">{{ translate("Milestone due tomorrow") }}</template>
										<template v-else>{{ translate("{days} days to milestone", { days: project.days_to_milestone }) }}</template>
									</span>
								</div>
							</div>
						</div>
					</div>

					<!-- LIST VIEW -->
					<div v-else class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
						<!-- List header -->
						<div class="grid grid-cols-[minmax(0,2fr)_repeat(4,minmax(0,1fr))] gap-4 px-4 py-2.5 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
							<button class="flex items-center gap-1 text-left hover:text-gray-700 dark:hover:text-gray-300" @click="toggleSort('project_name')">
								{{ translate("Project") }}
								<component :is="sortIcon('project_name')" class="w-3 h-3" />
							</button>
							<button class="flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-300" @click="toggleSort('percent_complete')">
								{{ translate("Progress") }}
								<component :is="sortIcon('percent_complete')" class="w-3 h-3" />
							</button>
							<button class="flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-300" @click="toggleSort('expected_end_date')">
								{{ translate("Deadline") }}
								<component :is="sortIcon('expected_end_date')" class="w-3 h-3" />
							</button>
							<span>{{ translate("Manager") }}</span>
							<button class="flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-300" @click="toggleSort('task_count')">
								{{ translate("Tasks") }}
								<component :is="sortIcon('task_count')" class="w-3 h-3" />
							</button>
						</div>

						<!-- List rows -->
						<div
							v-for="project in filteredActiveProjects"
							:key="project.name"
							@click="openProject(project.name)"
							class="grid grid-cols-[minmax(0,2fr)_repeat(4,minmax(0,1fr))] gap-4 px-4 py-3 border-b border-gray-100 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer group transition-colors"
						>
							<!-- Name -->
							<div class="flex items-center gap-2 min-w-0">
								<img
									v-if="project.customer_image"
									:src="project.customer_image"
									:alt="project.customer_name"
									class="w-6 h-6 rounded object-contain border border-gray-100 dark:border-gray-700 bg-white flex-shrink-0"
								/>
								<div
									v-else-if="project.customer_name"
									class="w-6 h-6 rounded flex items-center justify-center text-[10px] font-semibold bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 flex-shrink-0 select-none"
								>
									{{ customerInitials(project.customer_name) }}
								</div>
								<Folder v-else class="w-4 h-4 text-blue-600 flex-shrink-0" />
								<span class="font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 truncate text-sm">
									{{ project.project_name }}
								</span>
							</div>

							<!-- Progress -->
							<div class="flex items-center gap-2 min-w-0">
								<div class="flex-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden min-w-[40px]">
									<div
										class="h-full rounded-full transition-all"
										:class="getProgressColorClass(project.percent_complete || 0)"
										:style="{ width: (project.percent_complete || 0) + '%' }"
									></div>
								</div>
								<span class="text-xs text-gray-600 dark:text-gray-400 flex-shrink-0">{{ project.percent_complete || 0 }}%</span>
							</div>

							<!-- Deadline -->
							<div class="flex items-center gap-1.5 text-sm" :class="isOverdue(project) ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'">
								<Calendar v-if="project.expected_end_date" class="w-3.5 h-3.5 flex-shrink-0" />
								<span class="truncate">
									{{ project.expected_end_date ? formatDate(project.expected_end_date) : "—" }}
								</span>
							</div>

							<!-- Manager -->
							<div class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 min-w-0">
								<User v-if="project.project_manager_name" class="w-3.5 h-3.5 flex-shrink-0" />
								<span class="truncate">{{ project.project_manager_name || "—" }}</span>
							</div>

							<!-- Tasks -->
							<div class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
								<Users class="w-3.5 h-3.5 flex-shrink-0" />
								<span>{{ project.task_count || 0 }}</span>
								<span v-if="project.user_task_count" class="text-blue-600 dark:text-blue-400 text-xs">({{ project.user_task_count }} {{ translate("yours") }})</span>
							</div>
						</div>
					</div>
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
							<!-- GRID VIEW (completed) -->
							<div
								v-if="viewMode === 'grid'"
								class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
							>
								<div
									v-for="project in filteredCompletedProjects"
									:key="project.name"
									@click="openProject(project.name)"
									class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5 hover:border-green-300 dark:hover:border-green-600 hover:shadow-md transition-all cursor-pointer group opacity-75 hover:opacity-100"
								>
									<div class="flex items-start justify-between mb-3">
										<div class="flex items-center gap-2.5 min-w-0">
											<img
												v-if="project.customer_image"
												:src="project.customer_image"
												:alt="project.customer_name"
												class="w-8 h-8 rounded-md object-contain border border-gray-100 dark:border-gray-700 bg-white flex-shrink-0"
											/>
											<div
												v-else-if="project.customer_name"
												class="w-8 h-8 rounded-md flex items-center justify-center text-xs font-semibold bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 flex-shrink-0 select-none"
											>
												{{ customerInitials(project.customer_name) }}
											</div>
											<Folder v-else class="w-5 h-5 text-green-600 flex-shrink-0" />
											<h3 class="font-medium text-gray-900 dark:text-gray-100 group-hover:text-green-600 truncate">
												{{ project.project_name }}
											</h3>
										</div>
										<ChevronRight class="w-5 h-5 text-gray-400 group-hover:text-green-600 transition-colors flex-shrink-0" />
									</div>

									<div class="mb-3">
										<span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full text-xs font-medium">
											<CheckCircle2 class="w-3 h-3" />
											{{ translate("Completed") }}
										</span>
									</div>

									<div class="space-y-1.5">
										<div v-if="project.expected_end_date" class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
											<Calendar class="w-3.5 h-3.5" />
											<span>{{ formatDate(project.expected_end_date) }}</span>
										</div>
										<div v-if="project.project_manager_name" class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
											<User class="w-3.5 h-3.5" />
											<span class="truncate">{{ project.project_manager_name }}</span>
										</div>
										<div class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
											<Users class="w-3.5 h-3.5" />
											<span>{{ project.task_count || 0 }} {{ translate("tasks") }}</span>
										</div>
									</div>
								</div>
							</div>

							<!-- LIST VIEW (completed) -->
							<div v-else class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
								<div class="grid grid-cols-[minmax(0,2fr)_repeat(4,minmax(0,1fr))] gap-4 px-4 py-2.5 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
									<span>{{ translate("Project") }}</span>
									<span>{{ translate("Progress") }}</span>
									<span>{{ translate("Deadline") }}</span>
									<span>{{ translate("Manager") }}</span>
									<span>{{ translate("Tasks") }}</span>
								</div>
								<div
									v-for="project in filteredCompletedProjects"
									:key="project.name"
									@click="openProject(project.name)"
									class="grid grid-cols-[minmax(0,2fr)_repeat(4,minmax(0,1fr))] gap-4 px-4 py-3 border-b border-gray-100 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer group transition-colors opacity-75 hover:opacity-100"
								>
									<div class="flex items-center gap-2 min-w-0">
										<img
											v-if="project.customer_image"
											:src="project.customer_image"
											:alt="project.customer_name"
											class="w-6 h-6 rounded object-contain border border-gray-100 dark:border-gray-700 bg-white flex-shrink-0"
										/>
										<div
											v-else-if="project.customer_name"
											class="w-6 h-6 rounded flex items-center justify-center text-[10px] font-semibold bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 flex-shrink-0 select-none"
										>
											{{ customerInitials(project.customer_name) }}
										</div>
										<Folder v-else class="w-4 h-4 text-green-600 flex-shrink-0" />
										<span class="font-medium text-gray-900 dark:text-gray-100 group-hover:text-green-600 truncate text-sm">{{ project.project_name }}</span>
									</div>
									<div class="flex items-center gap-1.5">
										<CheckCircle2 class="w-3.5 h-3.5 text-green-600 flex-shrink-0" />
										<span class="text-xs text-green-700 dark:text-green-400">100%</span>
									</div>
									<div class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
										<Calendar v-if="project.expected_end_date" class="w-3.5 h-3.5 flex-shrink-0" />
										<span class="truncate">{{ project.expected_end_date ? formatDate(project.expected_end_date) : "—" }}</span>
									</div>
									<div class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 min-w-0">
										<User v-if="project.project_manager_name" class="w-3.5 h-3.5 flex-shrink-0" />
										<span class="truncate">{{ project.project_manager_name || "—" }}</span>
									</div>
									<div class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
										<Users class="w-3.5 h-3.5 flex-shrink-0" />
										<span>{{ project.task_count || 0 }}</span>
									</div>
								</div>
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
