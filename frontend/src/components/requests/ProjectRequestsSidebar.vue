<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import dayjs from "dayjs";
import {
	Check,
	ChevronDown,
	ChevronRight,
	ClipboardList,
	ExternalLink,
	GitPullRequestArrow,
	Hand,
	UserCheck,
	UserMinus,
	Plus,
	Info,
	RefreshCw,
	Search,
	X,
} from "lucide-vue-next";
import CustomerRequestModal from "./CustomerRequestModal.vue";
import RequestsGuideModal from "./RequestsGuideModal.vue";
import { translate } from "../../utils/translation";
import {
	CUSTOMER_REQUEST_PIPELINE,
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

const emit = defineEmits(["close", "refresh", "open-task"]);

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
const showGuide = ref(false);
const modalSubject = ref("");
const modalSource = ref("");

// Workflow actions: the request being moved stays busy until the refetch the
// action triggers has finished, so its old buttons cannot be clicked twice.
const busyRequest = ref("");
const actionErrors = ref({});

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

function pipelineStepClass(request, step) {
	const state = request.workflow_state || "Draft";
	if (state === "Rejected") return "bg-gray-200 dark:bg-gray-600";
	const current = CUSTOMER_REQUEST_PIPELINE.indexOf(state);
	const index = CUSTOMER_REQUEST_PIPELINE.indexOf(step);
	if (index < current) return "bg-green-500";
	if (index === current) return "bg-green-600 ring-2 ring-green-200 dark:ring-green-900";
	return "bg-gray-200 dark:bg-gray-600";
}

function actionButtonClass(action) {
	if (action.next_state === "Rejected") {
		return "border border-red-200 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-900/30";
	}
	return "bg-green-600 text-white hover:bg-green-700";
}

function setActionError(name, message) {
	actionErrors.value = { ...actionErrors.value, [name]: message };
}

const currentUser = computed(() => realWindow?.frappe?.session?.user || "");

function isAssignedToMe(request) {
	return (request.assigned_to || []).some((assignee) => assignee.user === currentUser.value);
}

function assigneeNames(request) {
	return (request.assigned_to || []).map((assignee) => assignee.full_name || assignee.user).join(", ");
}

function hasEstimate(request) {
	return Boolean(request.estimated_hours || request.estimated_amount || request.quotation);
}

function movedMessage(request, result) {
	return translate("{0} moved to {1}", [request.name, translate(result?.workflow_state || "")]);
}

async function runRequestAction(request, method, payload, confirmMessage, successMessage = movedMessage) {
	if (busyRequest.value) return;
	if (confirmMessage && !realWindow?.confirm(confirmMessage)) return;

	busyRequest.value = request.name;
	setActionError(request.name, "");
	try {
		const result = await apiPost(method, { name: request.name, ...payload });
		showAlert(successMessage(request, result), "green");
		emit("refresh");
		// The parent's loading flag reaches this component's props on the next
		// render; until then props.loading still reads the pre-refresh value.
		await nextTick();
		if (!props.loading) busyRequest.value = "";
	} catch (err) {
		console.error("Failed to change customer request state:", err);
		setActionError(request.name, decodeApiError(err, translate("Status could not be changed")));
		busyRequest.value = "";
	}
}

function applyAction(request, action) {
	const confirmMessage =
		action.next_state === "Rejected" ? translate("Reject request \"{0}\"?", [request.subject]) : "";
	return runRequestAction(
		request,
		"erpnext_projekt_hub.api.project_hub.apply_customer_request_action",
		{ action: action.action },
		confirmMessage
	);
}

function createChangeRequest(request) {
	return runRequestAction(
		request,
		"erpnext_projekt_hub.api.project_hub.create_change_request_from_customer_request",
		{},
		translate("Create a change request for \"{0}\"?", [request.subject])
	);
}

function takeRequest(request) {
	return runRequestAction(
		request,
		"erpnext_projekt_hub.api.project_hub.take_customer_request",
		{},
		"",
		() => translate("You are now analyzing {0}", [request.name])
	);
}

function releaseRequest(request) {
	return runRequestAction(
		request,
		"erpnext_projekt_hub.api.project_hub.release_customer_request",
		{},
		"",
		() => translate("{0} is back in the analysis queue", [request.name])
	);
}

watch(
	() => props.loading,
	(loading) => {
		if (!loading) busyRequest.value = "";
	}
);

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
				<button
					type="button"
					class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-blue-600 dark:hover:bg-gray-700 dark:hover:text-blue-400"
					:title="translate('How requests work')"
					:aria-label="translate('How requests work')"
					@click="showGuide = true"
				>
					<Info class="w-4 h-4" />
				</button>
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
									<div
										v-if="request.workflow_state === 'To Analyze'"
										class="mt-1 flex items-center gap-1 text-xs"
									>
										<template v-if="request.assigned_to?.length">
											<UserCheck class="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
											<span class="text-gray-600 dark:text-gray-300">
												{{ translate("Analyzed by: {0}", [assigneeNames(request)]) }}
											</span>
										</template>
										<span v-else class="font-medium text-amber-700 dark:text-amber-400">
											{{ translate("Waiting for someone to analyze") }}
										</span>
									</div>
									<div
										v-if="!expanded.has(request.name) && hasEstimate(request)"
										class="mt-1 flex flex-wrap gap-x-2 text-xs font-medium text-gray-700 dark:text-gray-200"
									>
										<span v-if="request.estimated_hours">{{ request.estimated_hours }} h</span>
										<span v-if="request.estimated_amount">
											· {{ formatRequestAmount(request, "estimated_amount") }}
										</span>
										<span v-if="request.quotation" class="font-normal text-gray-500 dark:text-gray-400">
											· {{ request.quotation }}
										</span>
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
							<div>
								<div class="flex items-center gap-1" :title="translate(request.workflow_state || 'Draft')">
									<div
										v-for="step in CUSTOMER_REQUEST_PIPELINE"
										:key="step"
										:class="['h-1.5 flex-1 rounded-full', pipelineStepClass(request, step)]"
									></div>
								</div>
								<div class="mt-1 flex justify-between text-[10px] text-gray-400">
									<span
										v-for="step in CUSTOMER_REQUEST_PIPELINE"
										:key="step"
										:class="{ 'font-semibold text-green-700 dark:text-green-400': step === (request.workflow_state || 'Draft') }"
									>
										{{ translate(step) }}
									</span>
								</div>
								<div
									v-if="request.workflow_state === 'Rejected'"
									class="mt-1 text-xs font-medium text-red-600 dark:text-red-400"
								>
									{{ translate("Rejected") }}
								</div>
							</div>
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

						<div
							v-if="request.workflow_state === 'To Analyze' || request.actions?.length || request.can_create_change_request || actionErrors[request.name]"
							class="border-t border-gray-100 dark:border-gray-700 px-3 py-2"
						>
							<div
								v-if="request.workflow_state === 'To Analyze'"
								class="mb-1.5 flex flex-wrap items-center gap-1.5"
							>
								<button
									v-if="!isAssignedToMe(request)"
									type="button"
									:disabled="Boolean(busyRequest)"
									class="inline-flex items-center gap-1 rounded-md bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
									@click="takeRequest(request)"
								>
									<Hand class="h-3.5 w-3.5" />
									{{ translate("Take for analysis") }}
								</button>
								<button
									v-else
									type="button"
									:disabled="Boolean(busyRequest)"
									class="inline-flex items-center gap-1 rounded-md border border-gray-200 dark:border-gray-600 px-2 py-1 text-xs text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
									@click="releaseRequest(request)"
								>
									<UserMinus class="h-3.5 w-3.5" />
									{{ translate("Release") }}
								</button>
								<button
									type="button"
									class="inline-flex items-center gap-1 rounded-md border border-blue-200 dark:border-blue-800 px-2 py-1 text-xs font-medium text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/30"
									@click="openInDesk('Customer Request', request.name)"
								>
									<ExternalLink class="h-3.5 w-3.5" />
									{{ translate("Analyze in Desk") }}
								</button>
							</div>
							<div class="flex flex-wrap items-center gap-1.5">
								<button
									v-for="action in request.actions || []"
									:key="action.action"
									type="button"
									:disabled="Boolean(busyRequest)"
									:title="translate('Move to: {0}', [translate(action.next_state)])"
									:class="[
										'inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50',
										actionButtonClass(action),
									]"
									@click="applyAction(request, action)"
								>
									<X v-if="action.next_state === 'Rejected'" class="h-3.5 w-3.5" />
									<Check v-else class="h-3.5 w-3.5" />
									{{ translate(action.action) }}
								</button>
								<button
									v-if="request.can_create_change_request"
									type="button"
									:disabled="Boolean(busyRequest)"
									class="inline-flex items-center gap-1 rounded-md bg-violet-600 px-2 py-1 text-xs font-medium text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
									@click="createChangeRequest(request)"
								>
									<GitPullRequestArrow class="h-3.5 w-3.5" />
									{{ translate("Create Change Request") }}
								</button>
								<RefreshCw
									v-if="busyRequest === request.name"
									class="h-3.5 w-3.5 animate-spin text-gray-400"
								/>
							</div>
							<p v-if="actionErrors[request.name]" class="mt-1 text-xs text-red-600 dark:text-red-400">
								{{ actionErrors[request.name] }}
							</p>
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

		<RequestsGuideModal :open="showGuide" @close="showGuide = false" />

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
