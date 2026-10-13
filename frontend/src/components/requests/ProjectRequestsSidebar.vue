<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import dayjs from "dayjs";
import {
	ChevronDown,
	ChevronRight,
	ClipboardList,
	ExternalLink,
	GitPullRequestArrow,
	Maximize2,
	Plus,
	RefreshCw,
	Search,
	X,
} from "lucide-vue-next";
import CustomerRequestModal from "./CustomerRequestModal.vue";
import { translate } from "../../utils/translation";
import {
	CUSTOMER_REQUEST_STATES,
	REQUEST_SOURCES,
	apiPost,
	decodeApiError,
	deskUrl,
	formatRequestAmount,
	getRequestStateClass,
	htmlToText,
	isOpenCustomerRequest,
	stripHtml,
} from "../../utils/customerRequests";

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
	project: {
		type: Object,
		default: null,
	},
	customerRequests: {
		type: Array,
		default: () => [],
	},
	changeRequests: {
		type: Array,
		default: () => [],
	},
	loading: {
		type: Boolean,
		default: false,
	},
	error: {
		type: String,
		default: "",
	},
});

const emit = defineEmits(["close", "refresh", "open-task", "open-all"]);

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;

const STATUS_FILTERS = [
	{ key: "open", label: "Active" },
	{ key: "closed", label: "Closed" },
	{ key: "all", label: "All" },
];

const statusFilter = ref("open");
const searchQuery = ref("");
const expanded = ref(new Set());
const changeRequestsOpen = ref(true);

const quickSubject = ref("");
const quickSource = ref("");
const quickCreating = ref(false);
const quickError = ref("");
const quickInputRef = ref(null);
const showModal = ref(false);
const modalSubject = ref("");
const modalSource = ref("");

const projectName = computed(() => props.project?.name || props.projectId);
const hasCustomer = computed(() => !props.project || Boolean(props.project.customer));

const openCount = computed(() => props.customerRequests.filter(isOpenCustomerRequest).length);
const closedCount = computed(() => props.customerRequests.length - openCount.value);
const filterCounts = computed(() => ({
	open: openCount.value,
	closed: closedCount.value,
	all: props.customerRequests.length,
}));

const filteredRequests = computed(() => {
	const query = searchQuery.value.trim().toLowerCase();
	return props.customerRequests.filter((request) => {
		const open = isOpenCustomerRequest(request);
		if (statusFilter.value === "open" && !open) return false;
		if (statusFilter.value === "closed" && open) return false;
		if (!query) return true;
		return [request.subject, request.name, request.requested_by_name, stripHtml(request.notes)].some(
			(value) => String(value || "").toLowerCase().includes(query)
		);
	});
});

// Requests grouped by workflow state, in pipeline order (Draft → Converted).
const groupedRequests = computed(() => {
	const groups = new Map();
	for (const request of filteredRequests.value) {
		const state = request.workflow_state || "Draft";
		if (!groups.has(state)) groups.set(state, []);
		groups.get(state).push(request);
	}
	const order = (state) => {
		const index = CUSTOMER_REQUEST_STATES.indexOf(state);
		return index === -1 ? CUSTOMER_REQUEST_STATES.length : index;
	};
	return [...groups.entries()]
		.sort(([a], [b]) => order(a) - order(b))
		.map(([state, requests]) => ({ state, requests }));
});

function formatDate(value) {
	return value ? dayjs(value).format("DD.MM.YYYY") : "";
}

function toggleExpanded(name) {
	const next = new Set(expanded.value);
	if (next.has(name)) {
		next.delete(name);
	} else {
		next.add(name);
	}
	expanded.value = next;
}

function openInDesk(doctype, name) {
	realWindow?.open(deskUrl(doctype, name), "_blank", "noopener,noreferrer");
}

function showAlert(message, indicator = "blue") {
	if (realWindow?.frappe?.show_alert) {
		realWindow.frappe.show_alert({ message, indicator });
	}
}

async function submitQuickRequest() {
	if (quickCreating.value) return;
	const subject = quickSubject.value.trim();
	if (!subject) {
		quickError.value = translate("Subject is required");
		return;
	}

	quickCreating.value = true;
	quickError.value = "";
	try {
		await apiPost("erpnext_projekt_hub.api.project_hub.create_customer_request", {
			project: projectName.value,
			subject,
			request_date: dayjs().format("YYYY-MM-DD"),
			source: quickSource.value,
		});
		quickSubject.value = "";
		showAlert(translate("Customer request created"), "green");
		// A new request lands in Draft, so make sure it is visible.
		if (statusFilter.value === "closed") statusFilter.value = "open";
		emit("refresh");
		await nextTick();
		quickInputRef.value?.focus();
	} catch (err) {
		console.error("Failed to create customer request:", err);
		quickError.value = decodeApiError(err, translate("Customer request could not be created"));
	} finally {
		quickCreating.value = false;
	}
}

function openFullForm() {
	modalSubject.value = quickSubject.value.trim();
	modalSource.value = quickSource.value;
	showModal.value = true;
}

function handleModalCreated() {
	showModal.value = false;
	quickSubject.value = "";
	quickError.value = "";
	if (statusFilter.value === "closed") statusFilter.value = "open";
	emit("refresh");
}

onMounted(() => {
	quickInputRef.value?.focus();
});
</script>

<template>
	<aside class="h-full w-[440px] max-w-[92vw] bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
		<header class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between gap-2">
			<div class="flex items-center gap-2 min-w-0">
				<ClipboardList class="w-4 h-4 text-green-600 flex-shrink-0" />
				<div class="min-w-0">
					<div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
						{{ translate("Customer Requests") }}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">
						{{ translate("{0} active of {1}", [openCount, customerRequests.length]) }}
					</div>
				</div>
			</div>
			<div class="flex items-center gap-1">
				<button
					type="button"
					class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
					:title="translate('Refresh')"
					:disabled="loading"
					@click="emit('refresh')"
				>
					<RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
				</button>
				<button
					type="button"
					class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
					:title="translate('Open all requests')"
					@click="emit('open-all')"
				>
					<Maximize2 class="w-4 h-4" />
				</button>
				<button
					type="button"
					class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
					@click="emit('close')"
				>
					<X class="w-4 h-4" />
				</button>
			</div>
		</header>

		<!-- Quick add: subject + source, Enter saves a Draft request -->
		<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 space-y-2">
			<div
				v-if="!hasCustomer"
				class="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-200"
			>
				{{ translate("Project must have a customer") }}
			</div>
			<form class="flex items-center gap-2" @submit.prevent="submitQuickRequest">
				<input
					ref="quickInputRef"
					v-model="quickSubject"
					type="text"
					:disabled="!hasCustomer || quickCreating"
					:placeholder="translate('New customer request – type and press Enter')"
					class="min-w-0 flex-1 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-100 dark:focus:ring-green-900/40 disabled:opacity-60"
					@input="quickError = ''"
				/>
				<button
					type="submit"
					:disabled="!hasCustomer || quickCreating || !quickSubject.trim()"
					class="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
				>
					<Plus class="w-4 h-4" />
					{{ quickCreating ? translate("Adding...") : translate("Add") }}
				</button>
			</form>
			<div class="flex items-center justify-between gap-2">
				<select
					v-model="quickSource"
					:disabled="!hasCustomer"
					class="rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1 text-xs text-gray-700 dark:text-gray-200"
				>
					<option value="">{{ translate("Select source") }}</option>
					<option v-for="source in REQUEST_SOURCES" :key="source" :value="source">
						{{ translate(source) }}
					</option>
				</select>
				<button
					type="button"
					:disabled="!hasCustomer"
					class="text-xs font-medium text-green-700 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300 disabled:opacity-50"
					@click="openFullForm"
				>
					{{ translate("Full form with details") }} →
				</button>
			</div>
			<p v-if="quickError" class="text-xs text-red-600 dark:text-red-400">{{ quickError }}</p>
		</div>

		<!-- Filters -->
		<div class="px-4 py-2 border-b border-gray-200 dark:border-gray-700 space-y-2">
			<div class="flex items-center gap-1">
				<button
					v-for="filter in STATUS_FILTERS"
					:key="filter.key"
					type="button"
					:class="[
						'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors',
						statusFilter === filter.key
							? 'bg-green-600 text-white'
							: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600',
					]"
					@click="statusFilter = filter.key"
				>
					{{ translate(filter.label) }}
					<span class="opacity-75">{{ filterCounts[filter.key] }}</span>
				</button>
			</div>
			<div class="relative">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
				<input
					v-model="searchQuery"
					type="text"
					:placeholder="translate('Search requests...')"
					class="w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 pl-9 pr-3 py-1.5 text-sm text-gray-900 dark:text-gray-100"
				/>
			</div>
		</div>

		<div class="flex-1 overflow-y-auto p-4 pb-24 space-y-5">
			<div
				v-if="error"
				class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-200"
			>
				{{ error }}
			</div>

			<div v-if="loading && customerRequests.length === 0" class="py-6 text-center text-sm text-gray-500">
				{{ translate("Loading") }}...
			</div>

			<div
				v-else-if="groupedRequests.length === 0"
				class="rounded-xl border border-dashed border-gray-300 dark:border-gray-600 px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400"
			>
				{{ customerRequests.length === 0 ? translate("No requests for this project") : translate("No requests match the filters") }}
			</div>

			<section v-for="group in groupedRequests" :key="group.state">
				<div class="mb-2 flex items-center gap-2">
					<span :class="['rounded-full px-2 py-0.5 text-[11px] font-semibold', getRequestStateClass(group.state)]">
						{{ translate(group.state) }}
					</span>
					<span class="text-xs text-gray-400">{{ group.requests.length }}</span>
				</div>

				<div class="space-y-2">
					<article
						v-for="request in group.requests"
						:key="request.name"
						class="rounded-xl border border-gray-200 dark:border-gray-700 hover:border-green-300 dark:hover:border-green-700 transition-colors"
					>
						<button
							type="button"
							class="w-full px-3 py-2.5 text-left"
							@click="toggleExpanded(request.name)"
						>
							<div class="flex items-start gap-2">
								<component
									:is="expanded.has(request.name) ? ChevronDown : ChevronRight"
									class="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-400"
								/>
								<div class="min-w-0 flex-1">
									<div class="text-sm font-medium text-gray-900 dark:text-gray-100">
										{{ request.subject }}
									</div>
									<div class="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-gray-500 dark:text-gray-400">
										<span>{{ request.name }}</span>
										<span v-if="request.request_date">· {{ formatDate(request.request_date) }}</span>
										<span v-if="request.source">· {{ translate(request.source) }}</span>
										<span v-if="request.requested_by_name">· {{ request.requested_by_name }}</span>
									</div>
									<p
										v-if="!expanded.has(request.name) && request.notes"
										class="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-2"
									>
										{{ stripHtml(request.notes) }}
									</p>
								</div>
							</div>
						</button>

						<div
							v-if="expanded.has(request.name)"
							class="border-t border-gray-100 dark:border-gray-700 px-3 py-3 space-y-3 text-sm"
						>
							<div v-if="request.notes">
								<div class="text-xs font-medium uppercase tracking-wide text-gray-400">
									{{ translate("Notes") }}
								</div>
								<p class="mt-1 whitespace-pre-line text-gray-700 dark:text-gray-200">
									{{ htmlToText(request.notes) }}
								</p>
							</div>
							<div v-if="request.business_value">
								<div class="text-xs font-medium uppercase tracking-wide text-gray-400">
									{{ translate("Business Value") }}
								</div>
								<p class="mt-1 whitespace-pre-line text-gray-700 dark:text-gray-200">
									{{ htmlToText(request.business_value) }}
								</p>
							</div>
							<div class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
								<span v-if="request.estimated_hours">
									{{ translate("Estimated Hours") }}: {{ request.estimated_hours }}h
								</span>
								<span v-if="request.estimated_amount">
									{{ translate("Estimated Amount") }}: {{ formatRequestAmount(request, "estimated_amount") }}
								</span>
								<span v-if="request.quotation">{{ translate("Quotation") }}: {{ request.quotation }}</span>
							</div>
							<div class="flex flex-wrap items-center gap-2">
								<button
									type="button"
									class="inline-flex items-center gap-1 rounded-md border border-gray-200 dark:border-gray-600 px-2 py-1 text-xs text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
									@click="openInDesk('Customer Request', request.name)"
								>
									<ExternalLink class="h-3.5 w-3.5" />
									{{ translate("Open in Desk") }}
								</button>
								<button
									v-if="request.change_request"
									type="button"
									class="inline-flex items-center gap-1 rounded-md border border-violet-200 dark:border-violet-800 px-2 py-1 text-xs text-violet-700 dark:text-violet-300 hover:bg-violet-50 dark:hover:bg-violet-900/30"
									@click="openInDesk('Change Request', request.change_request)"
								>
									<GitPullRequestArrow class="h-3.5 w-3.5" />
									{{ request.change_request }}
								</button>
							</div>
						</div>
					</article>
				</div>
			</section>

			<section v-if="changeRequests.length > 0" class="border-t border-gray-200 dark:border-gray-700 pt-4">
				<button
					type="button"
					class="mb-2 flex w-full items-center gap-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400"
					@click="changeRequestsOpen = !changeRequestsOpen"
				>
					<component :is="changeRequestsOpen ? ChevronDown : ChevronRight" class="h-4 w-4" />
					{{ translate("Change Requests") }}
					<span class="font-normal text-gray-400">{{ changeRequests.length }}</span>
				</button>
				<div v-if="changeRequestsOpen" class="space-y-2">
					<div
						v-for="changeRequest in changeRequests"
						:key="changeRequest.name"
						class="rounded-xl border border-gray-200 dark:border-gray-700 px-3 py-2.5"
					>
						<div class="flex items-start justify-between gap-2">
							<button
								type="button"
								class="min-w-0 text-left"
								@click="openInDesk('Change Request', changeRequest.name)"
							>
								<div class="text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-green-700 dark:hover:text-green-300">
									{{ changeRequest.subject }}
								</div>
								<div class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
									{{ changeRequest.name }}
									<span v-if="changeRequest.approved_hours">· {{ changeRequest.approved_hours }}h</span>
									<span v-if="changeRequest.approved_amount">
										· {{ formatRequestAmount(changeRequest, "approved_amount") }}
									</span>
								</div>
							</button>
							<span :class="['flex-shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold', getRequestStateClass(changeRequest.workflow_state)]">
								{{ translate(changeRequest.workflow_state || "Draft") }}
							</span>
						</div>
						<button
							v-if="changeRequest.task"
							type="button"
							class="mt-2 inline-flex items-center gap-1 rounded-md bg-blue-50 dark:bg-blue-900/30 px-2 py-1 text-xs text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50"
							@click="emit('open-task', changeRequest.task)"
						>
							{{ translate("Task") }}: {{ changeRequest.task }}
						</button>
					</div>
				</div>
			</section>
		</div>

		<CustomerRequestModal
			:open="showModal"
			:project="projectName"
			:project-label="project?.project_name || projectName"
			:customer="project?.customer_name || project?.customer || ''"
			:initial-subject="modalSubject"
			:initial-source="modalSource"
			@close="showModal = false"
			@created="handleModalCreated"
		/>
	</aside>
</template>
