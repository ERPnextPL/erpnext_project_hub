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
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import { translate } from "../utils/translation";
import { getProgressColorClass } from "../utils/progressColors";
const router = useRouter();
const activeProjects = ref([]);
const completedProjects = ref([]);
const isManager = ref(false);
const loading = ref(true);
const showCompleted = ref(false);

onMounted(async () => {
	try {
		const response = await fetch(
			"/api/method/erpnext_projekt_hub.api.project_hub.get_projects",
			{
				headers: {
					"X-Frappe-CSRF-Token": window.csrf_token,
				},
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

const hasProjects = computed(
	() => activeProjects.value.length > 0 || completedProjects.value.length > 0
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
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-10">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<Folder class="w-6 h-6 text-blue-600" />
						<h1 class="text-xl font-semibold text-gray-900">
							{{ translate("Projects") }}
						</h1>
					</div>
					<div class="flex items-center gap-3 sm:gap-4">
						<OutlinerNav />
						<a
							href="/app"
							class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 whitespace-nowrap"
						>
							← {{ translate("Back to Desk") }}
						</a>
					</div>
				</div>
			</div>
		</header>

		<!-- Content -->
		<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
			<!-- Header with info -->
			<div class="mb-6 flex items-center justify-between">
				<div>
					<h2 class="text-lg font-medium text-gray-900">
						{{ isManager ? translate("All projects") : translate("My projects") }}
					</h2>
					<p class="text-sm text-gray-500">
						{{
							isManager
								? translate("Manage all projects")
								: translate("Projects with assigned tasks")
						}}
					</p>
				</div>
				<div class="flex items-center gap-2 text-sm text-gray-500">
					<span class="px-2 py-1 bg-blue-50 text-blue-700 rounded-md">
						{{ activeProjects.length }} {{ translate("active") }}
					</span>
					<span
						v-if="completedProjects.length > 0"
						class="px-2 py-1 bg-green-50 text-green-700 rounded-md"
					>
						{{ completedProjects.length }} {{ translate("completed") }}
					</span>
				</div>
			</div>

			<!-- Loading state -->
			<div v-if="loading" class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			</div>

			<!-- Empty state -->
			<div
				v-else-if="!hasProjects"
				class="text-center py-12 bg-white rounded-lg border border-gray-200"
			>
				<Folder class="w-12 h-12 text-gray-400 mx-auto mb-4" />
				<h3 class="text-lg font-medium text-gray-900 mb-2">
					{{ translate("No projects found") }}
				</h3>
				<p class="text-gray-500">
					{{
						isManager
							? translate("Create a project in ERPNext to get started.")
							: translate("You don't have any tasks assigned to projects yet.")
					}}
				</p>
			</div>

			<div v-else>
				<!-- Active Projects Section -->
				<section v-if="activeProjects.length > 0" class="mb-8">
					<h3
						class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2"
					>
						<Folder class="w-4 h-4" />
						{{ translate("Active projects") }} ({{ activeProjects.length }})
					</h3>
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						<div
							v-for="project in activeProjects"
							:key="project.name"
							@click="openProject(project.name)"
							class="bg-white rounded-lg border border-gray-200 p-5 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
						>
							<div class="flex items-start justify-between mb-3">
								<div class="flex items-center gap-2">
									<Folder class="w-5 h-5 text-blue-600" />
									<h3
										class="font-medium text-gray-900 group-hover:text-blue-600"
									>
										{{ project.project_name }}
									</h3>
								</div>
								<ChevronRight
									class="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors"
								/>
							</div>

							<!-- Progress bar -->
							<div class="mb-3">
								<div class="flex items-center justify-between text-xs mb-1">
									<span class="text-gray-500">{{ translate("Progress") }}</span>
									<span class="font-medium text-gray-700"
										>{{ project.percent_complete || 0 }}%</span
									>
								</div>
								<div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
									<div
										class="h-full rounded-full transition-all duration-300"
										:class="getProgressColorClass(project.percent_complete || 0)"
										:style="{ width: (project.percent_complete || 0) + '%' }"
									></div>
								</div>
							</div>

							<div class="space-y-2">
								<div class="flex items-center gap-2 text-sm text-gray-500">
									<span
										:class="[
											'px-2 py-0.5 rounded-full text-xs font-medium',
											getStatusClass(project.status),
										]"
									>
										{{ project.status }}
									</span>
								</div>

								<div
									v-if="project.expected_end_date"
									class="flex items-center gap-1.5 text-sm text-gray-500"
								>
									<Calendar class="w-4 h-4" />
									<span
										>{{ translate("Due") }}
										{{ project.expected_end_date }}</span
									>
								</div>

								<div class="flex items-center gap-3 text-sm text-gray-500">
									<div class="flex items-center gap-1.5">
										<Users class="w-4 h-4" />
										<span
											>{{ project.task_count || 0 }}
											{{ translate("tasks") }}</span
										>
									</div>
									<div
										v-if="project.user_task_count"
										class="flex items-center gap-1.5 text-blue-600"
									>
										<span
											>{{ project.user_task_count }}
											{{ translate("yours") }}</span
										>
									</div>
								</div>

								<!-- Assigned users count -->
								<div
									v-if="project.assigned_users_count > 0"
									class="flex items-center gap-1.5 text-sm text-gray-500"
								>
									<Users class="w-4 h-4 text-purple-500" />
									<span
										>{{ project.assigned_users_count }}
										{{
											project.assigned_users_count === 1
												? translate("person")
												: translate("people")
										}}</span
									>
								</div>

								<!-- Next milestone -->
								<div
									v-if="project.next_milestone"
									class="flex items-center gap-1.5 text-sm"
								>
									<Flag class="w-4 h-4 text-amber-500" />
									<span
										:class="[
											project.days_to_milestone < 0
												? 'text-red-600 font-medium'
												: project.days_to_milestone <= 3
												? 'text-amber-600 font-medium'
												: 'text-gray-500',
										]"
									>
										<template v-if="project.days_to_milestone < 0">
											{{ translate("Milestone overdue") }}
										</template>
										<template v-else-if="project.days_to_milestone === 0">
											{{ translate("Milestone due today") }}
										</template>
										<template v-else-if="project.days_to_milestone === 1">
											{{ translate("Milestone due tomorrow") }}
										</template>
										<template v-else>
											{{
												translate("{days} days to milestone", {
													days: project.days_to_milestone,
												})
											}}
										</template>
									</span>
								</div>
							</div>
						</div>
					</div>
				</section>

				<!-- Completed Projects Section -->
				<section v-if="completedProjects.length > 0">
					<!-- Toggle button -->
					<button
						@click="showCompleted = !showCompleted"
						class="w-full flex items-center justify-between py-3 px-4 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors mb-4"
					>
						<div class="flex items-center gap-2 text-sm font-semibold text-gray-600">
							<Archive class="w-4 h-4" />
							<span
								>{{ translate("Completed projects") }} ({{
									completedProjects.length
								}})</span
							>
						</div>
						<div class="flex items-center gap-2 text-gray-500">
							<span class="text-xs">{{
								showCompleted ? translate("Hide") : translate("Show")
							}}</span>
							<ChevronDown
								class="w-4 h-4 transition-transform duration-200"
								:class="showCompleted ? 'rotate-180' : ''"
							/>
						</div>
					</button>

					<!-- Completed projects grid (collapsible) -->
					<Transition name="slide-fade">
						<div
							v-if="showCompleted"
							class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
						>
							<div
								v-for="project in completedProjects"
								:key="project.name"
								@click="openProject(project.name)"
								class="bg-white rounded-lg border border-gray-200 p-5 hover:border-green-300 hover:shadow-md transition-all cursor-pointer group opacity-75 hover:opacity-100"
							>
								<div class="flex items-start justify-between mb-3">
									<div class="flex items-center gap-2">
										<CheckCircle2 class="w-5 h-5 text-green-600" />
										<h3
											class="font-medium text-gray-900 group-hover:text-green-600"
										>
											{{ project.project_name }}
										</h3>
									</div>
									<ChevronRight
										class="w-5 h-5 text-gray-400 group-hover:text-green-600 transition-colors"
									/>
								</div>

								<!-- Completed badge -->
								<div class="mb-3">
									<span
										class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium"
									>
										<CheckCircle2 class="w-3 h-3" />
										{{ translate("Completed") }}
									</span>
								</div>

								<div class="space-y-2">
									<div
										v-if="project.expected_end_date"
										class="flex items-center gap-1.5 text-sm text-gray-500"
									>
										<Calendar class="w-4 h-4" />
										<span
											>{{ translate("Completed") }}
											{{ project.expected_end_date }}</span
										>
									</div>

									<div class="flex items-center gap-1.5 text-sm text-gray-500">
										<Users class="w-4 h-4" />
										<span
											>{{ project.task_count || 0 }}
											{{ translate("tasks") }}</span
										>
									</div>
								</div>
							</div>
						</div>
					</Transition>
				</section>
			</div>
		</main>
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
