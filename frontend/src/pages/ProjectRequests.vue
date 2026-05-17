<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { ClipboardList, ExternalLink, RefreshCw } from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import { translate } from "../utils/translation";

const projects = ref([]);
const selectedProject = ref("");
const projectInfo = ref(null);
const customerRequests = ref([]);
const changeRequests = ref([]);
const loadingProjects = ref(true);
const loadingRequests = ref(false);
const error = ref("");

const hasRequests = computed(
	() => customerRequests.value.length > 0 || changeRequests.value.length > 0
);

function getCsrfToken() {
	if (window.frappe?.csrf_token && window.frappe.csrf_token !== "None") {
		return window.frappe.csrf_token;
	}
	if (window.csrf_token && window.csrf_token !== "{{ csrf_token }}") {
		return window.csrf_token;
	}
	return "";
}

async function apiGet(method, params = {}) {
	const query = new URLSearchParams(params);
	const response = await fetch(`/api/method/${method}?${query.toString()}`, {
		headers: {
			"X-Frappe-CSRF-Token": getCsrfToken(),
		},
	});
	const data = await response.json();
	if (!response.ok || data.exc) {
		throw new Error(data.exception || data._server_messages || "API Error");
	}
	return data.message;
}

async function fetchProjects() {
	loadingProjects.value = true;
	error.value = "";
	try {
		const result = await apiGet("erpnext_projekt_hub.api.project_hub.get_projects");
		projects.value = [...(result.active || []), ...(result.completed || [])];
		if (!selectedProject.value && projects.value.length > 0) {
			selectedProject.value = projects.value[0].name;
		}
	} catch (err) {
		console.error("Failed to fetch projects:", err);
		error.value = translate("Project requests failed to load");
	} finally {
		loadingProjects.value = false;
	}
}

async function fetchRequests() {
	if (!selectedProject.value) {
		customerRequests.value = [];
		changeRequests.value = [];
		projectInfo.value = null;
		return;
	}

	loadingRequests.value = true;
	error.value = "";
	try {
		const result = await apiGet("erpnext_projekt_hub.api.project_hub.get_project_requests", {
			project: selectedProject.value,
		});
		projectInfo.value = result.project || null;
		customerRequests.value = result.customer_requests || [];
		changeRequests.value = result.change_requests || [];
	} catch (err) {
		console.error("Failed to fetch project requests:", err);
		error.value = translate("Project requests failed to load");
	} finally {
		loadingRequests.value = false;
	}
}

function openDesk(doctype, name) {
	const route = doctype.toLowerCase().replaceAll(" ", "-");
	window.location.href = `/app/${route}/${name}`;
}

function openDeskList(doctype) {
	const route = doctype.toLowerCase().replaceAll(" ", "-");
	window.location.href = `/app/${route}`;
}

function formatAmount(row, amountField) {
	const amount = row[amountField];
	if (amount === null || amount === undefined || amount === "") return "-";
	return `${amount} ${row.currency || ""}`.trim();
}

onMounted(fetchProjects);

watch(selectedProject, () => {
	fetchRequests();
});
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="w-full px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<ClipboardList class="w-6 h-6 text-emerald-600" />
						<h1 class="text-xl font-semibold text-gray-900">
							{{ translate("Requests") }}
						</h1>
					</div>
					<OutlinerNav />
				</div>
			</div>
		</header>

		<main class="w-full px-4 sm:px-6 lg:px-8 py-6">
			<div class="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
				<div>
					<h2 class="text-lg font-medium text-gray-900">
						{{ projectInfo?.project_name || translate("Project requests") }}
					</h2>
					<p class="text-sm text-gray-500">
						{{ translate("Customer requests and approved change requests") }}
					</p>
				</div>

				<div class="flex flex-col gap-2 sm:flex-row sm:items-center">
					<select
						v-model="selectedProject"
						class="h-10 min-w-[260px] rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100"
						:disabled="loadingProjects"
					>
						<option value="">{{ translate("Select project") }}</option>
						<option v-for="project in projects" :key="project.name" :value="project.name">
							{{ project.project_name || project.name }}
						</option>
					</select>
					<button
						type="button"
						class="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-gray-300 bg-white px-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
						:disabled="loadingRequests"
						@click="fetchRequests"
					>
						<RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loadingRequests }" />
						{{ translate("Refresh") }}
					</button>
				</div>
			</div>

			<div v-if="error" class="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
				{{ error }}
			</div>

			<div v-if="loadingProjects || loadingRequests" class="flex items-center justify-center py-12">
				<div class="h-8 w-8 animate-spin rounded-full border-b-2 border-emerald-600"></div>
			</div>

			<div
				v-else-if="!selectedProject"
				class="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500"
			>
				{{ translate("Select project") }}
			</div>

			<div
				v-else-if="!hasRequests"
				class="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500"
			>
				{{ translate("No requests for this project") }}
			</div>

			<div v-else class="grid grid-cols-1 gap-5 xl:grid-cols-2">
				<section class="rounded-lg border border-gray-200 bg-white">
					<div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
						<h3 class="text-sm font-semibold uppercase tracking-wide text-gray-500">
							{{ translate("Customer Requests") }}
						</h3>
						<button
							type="button"
							class="inline-flex items-center gap-1 text-sm text-emerald-700 hover:text-emerald-900"
							@click="openDeskList('Customer Request')"
						>
							{{ translate("Open list") }}
							<ExternalLink class="h-4 w-4" />
						</button>
					</div>
					<div class="divide-y divide-gray-100">
						<button
							v-for="request in customerRequests"
							:key="request.name"
							type="button"
							class="block w-full px-4 py-3 text-left hover:bg-gray-50"
							@click="openDesk('Customer Request', request.name)"
						>
							<div class="flex items-start justify-between gap-3">
								<div>
									<div class="font-medium text-gray-900">{{ request.subject }}</div>
									<div class="mt-1 text-xs text-gray-500">{{ request.name }}</div>
								</div>
								<span class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700">
									{{ translate(request.workflow_state || "Draft") }}
								</span>
							</div>
							<div class="mt-2 flex flex-wrap gap-3 text-sm text-gray-500">
								<span>{{ request.request_date || "-" }}</span>
								<span>{{ request.estimated_hours || 0 }}h</span>
								<span>{{ formatAmount(request, "estimated_amount") }}</span>
							</div>
						</button>
					</div>
				</section>

				<section class="rounded-lg border border-gray-200 bg-white">
					<div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
						<h3 class="text-sm font-semibold uppercase tracking-wide text-gray-500">
							{{ translate("Change Requests") }}
						</h3>
						<button
							type="button"
							class="inline-flex items-center gap-1 text-sm text-emerald-700 hover:text-emerald-900"
							@click="openDeskList('Change Request')"
						>
							{{ translate("Open list") }}
							<ExternalLink class="h-4 w-4" />
						</button>
					</div>
					<div class="divide-y divide-gray-100">
						<button
							v-for="request in changeRequests"
							:key="request.name"
							type="button"
							class="block w-full px-4 py-3 text-left hover:bg-gray-50"
							@click="openDesk('Change Request', request.name)"
						>
							<div class="flex items-start justify-between gap-3">
								<div>
									<div class="font-medium text-gray-900">{{ request.subject }}</div>
									<div class="mt-1 text-xs text-gray-500">{{ request.name }}</div>
								</div>
								<span class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700">
									{{ translate(request.workflow_state || "Draft") }}
								</span>
							</div>
							<div class="mt-2 flex flex-wrap gap-3 text-sm text-gray-500">
								<span>{{ request.approved_hours || 0 }}h</span>
								<span>{{ formatAmount(request, "approved_amount") }}</span>
								<span v-if="request.task">{{ translate("Task") }}: {{ request.task }}</span>
							</div>
						</button>
					</div>
				</section>
			</div>
		</main>
	</div>
</template>
