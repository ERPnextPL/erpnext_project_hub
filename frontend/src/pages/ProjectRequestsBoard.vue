<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useDebounceFn } from "@vueuse/core";
import dayjs from "dayjs";
import {
	CalendarDays,
	ExternalLink,
	Plus,
	RefreshCw,
	Search,
	SquareKanban,
} from "lucide-vue-next";
import RequestsKanban from "../components/requests/RequestsKanban.vue";
import RequestBoardCard from "../components/requests/RequestBoardCard.vue";
import RequestDetailDrawer from "../components/requests/RequestDetailDrawer.vue";
import ChangeRequestCard from "../components/requests/ChangeRequestCard.vue";
import ChangeRequestDrawer from "../components/requests/ChangeRequestDrawer.vue";
import CustomerRequestModal from "../components/requests/CustomerRequestModal.vue";
import { useProjectRequests } from "../composables/useProjectRequests";
import { useCustomerRequestActions } from "../composables/useCustomerRequestActions";
import { translate } from "../utils/translation";
import { readFilters, writeFilters } from "../utils/urlFilters";
import { notifyRequestsChanged } from "../utils/requestsChannel";
import {
	CONVERTED_STATE,
	REJECTED_STATE,
	REQUEST_SOURCES,
	buildBoardColumns,
	filterBoardRequests,
	formatAmounts,
	formatNumber,
	getRequestMoves,
	isOpenCustomerRequest,
	sumAmounts,
} from "../utils/customerRequests";
import {
	CHANGE_REQUEST_BOARD_COLUMNS,
	CHANGE_REQUEST_STATE_ALIASES,
	filterChangeRequests,
	getChangeRequestMoves,
	isOpenChangeRequest,
} from "../utils/changeRequests";

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
});

const route = useRoute();
const router = useRouter();
const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const currentUser = realWindow?.frappe?.session?.user || "";

const {
	customerRequests,
	changeRequests,
	project,
	lastLoadedAt,
	loading,
	error,
	available,
	fetchRequests,
} = useProjectRequests(() => props.projectId);

// --- Toasts -----------------------------------------------------------------

const toasts = ref([]);
let toastId = 0;

function notify(message, kind = "success") {
	if (!message) return;
	const id = ++toastId;
	toasts.value = [...toasts.value, { id, message, kind }];
	setTimeout(() => {
		toasts.value = toasts.value.filter((toast) => toast.id !== id);
	}, kind === "error" ? 6000 : 3500);
}

const {
	busyRequest,
	applyAction: runWorkflowAction,
	applyChangeRequestAction,
	createChangeRequest,
	takeRequest,
	releaseRequest,
	saveAnalysis,
} = useCustomerRequestActions(() => props.projectId, { refresh: fetchRequests, notify });

// --- Filters (kept in the URL) ----------------------------------------------

const ASSIGNMENT_FILTERS = [
	{ key: "all", label: "All" },
	{ key: "mine", label: "Mine" },
	{ key: "unassigned", label: "Unassigned" },
];
const PERIODS = [
	{ value: "", label: "Any date" },
	{ value: "7", label: "Last 7 days" },
	{ value: "30", label: "Last 30 days" },
	{ value: "90", label: "Last 90 days" },
];
const CANCELLED_STATE = "Cancelled";

// The board shows customer requests or change requests (view=change).
const VIEW_TABS = [
	{ key: "customer", label: "Customer Requests" },
	{ key: "change", label: "Change Requests" },
];
const VIEWS = VIEW_TABS.map((view) => view.key);
const FILTER_DEFAULTS = { view: "customer", q: "", assigned: "all", source: "", period: "" };
const FILTER_SANITIZERS = {
	view: (value) => (VIEWS.includes(value) ? value : "customer"),
	assigned: (value) => (ASSIGNMENT_FILTERS.some((filter) => filter.key === value) ? value : "all"),
	source: (value) => (REQUEST_SOURCES.includes(value) ? value : ""),
	period: (value) => (PERIODS.some((period) => period.value === value) ? value : ""),
};

const filters = ref(readFilters(route, FILTER_DEFAULTS, FILTER_SANITIZERS));
const searchInput = ref(null);
const syncFiltersToUrl = useDebounceFn(
	() => writeFilters(router, route, filters.value, FILTER_DEFAULTS),
	300
);
watch(filters, syncFiltersToUrl, { deep: true });

const isChangeView = computed(() => filters.value.view === "change");

function setView(view) {
	if (filters.value.view === view) return;
	filters.value.view = view;
	selectedName.value = "";
}

// --- Board data -------------------------------------------------------------

// Target state of requests being moved, shown before the server confirms.
const pendingStates = ref({});
const now = ref(new Date());

function withPendingStates(requests) {
	return requests.map((request) =>
		pendingStates.value[request.name]
			? { ...request, workflow_state: pendingStates.value[request.name] }
			: request
	);
}

const boardCustomerRequests = computed(() => withPendingStates(customerRequests.value));
const boardChangeRequests = computed(() => withPendingStates(changeRequests.value));
const boardRequests = computed(() =>
	isChangeView.value ? boardChangeRequests.value : boardCustomerRequests.value
);
const visibleRequests = computed(() =>
	isChangeView.value
		? filterChangeRequests(boardRequests.value, filters.value, now.value)
		: filterBoardRequests(boardRequests.value, filters.value, currentUser, now.value)
);
const columns = computed(() =>
	isChangeView.value
		? buildBoardColumns(visibleRequests.value, {
				columns: CHANGE_REQUEST_BOARD_COLUMNS,
				hoursField: "approved_hours",
				amountField: "approved_amount",
		  })
		: buildBoardColumns(visibleRequests.value)
);

const summary = computed(() => {
	const change = isChangeView.value;
	const hoursField = change ? "approved_hours" : "estimated_hours";
	const open = visibleRequests.value.filter(change ? isOpenChangeRequest : isOpenCustomerRequest);
	return {
		count: open.length,
		hours: open.reduce((total, request) => total + (Number(request[hoursField]) || 0), 0),
		amounts: formatAmounts(sumAmounts(open, change ? "approved_amount" : "estimated_amount")),
	};
});

const openCounts = computed(() => ({
	customer: customerRequests.value.filter(isOpenCustomerRequest).length,
	change: changeRequests.value.filter(isOpenChangeRequest).length,
}));

const hasCustomer = computed(() => !project.value || Boolean(project.value.customer));
const projectLabel = computed(() => project.value?.project_name || props.projectId);
const syncedAt = computed(() => (lastLoadedAt.value ? dayjs(lastLoadedAt.value).format("HH:mm") : ""));
const projectUrl = computed(() => `/project-hub/${encodeURIComponent(props.projectId)}`);

watch(
	projectLabel,
	(label) => {
		document.title = `${translate("Requests board")} · ${label}`;
	},
	{ immediate: true }
);

// --- Detail drawer ----------------------------------------------------------

const selectedName = ref("");
const selectedRequest = computed(
	() => boardRequests.value.find((request) => request.name === selectedName.value) || null
);
watch([customerRequests, changeRequests], () => {
	if (selectedName.value && !loading.value && !selectedRequest.value) selectedName.value = "";
});

function openRequest(request) {
	selectedName.value = request.name;
}

// The customer request a change request came from, or the other way round.
function openLinked(view, name) {
	setView(view);
	selectedName.value = name;
}

// --- Confirmation dialog ----------------------------------------------------

const confirmation = ref(null);

function askConfirmation(options) {
	return new Promise((resolve) => {
		confirmation.value = { ...options, resolve };
	});
}

function settleConfirmation(answer) {
	confirmation.value?.resolve(answer);
	confirmation.value = null;
}

// --- Changes ----------------------------------------------------------------

async function convertRequest(request) {
	const confirmed = await askConfirmation({
		title: translate("Create a change request?"),
		message: translate(
			"{0} will be marked as converted and a new Change Request will be created from its estimate.",
			[request.name]
		),
		confirmLabel: translate("Create Change Request"),
		tone: "violet",
	});
	if (!confirmed) return;

	pendingStates.value = { ...pendingStates.value, [request.name]: CONVERTED_STATE };
	await createChangeRequest(request);
	clearPending(request.name);
}

async function applyAction(request, action, nextState) {
	const change = isChangeView.value;
	if (!change && nextState === REJECTED_STATE) {
		const confirmed = await askConfirmation({
			title: translate("Reject request?"),
			message: translate("Reject request \"{0}\"?", [request.subject]),
			confirmLabel: translate("Reject"),
			tone: "red",
		});
		if (!confirmed) return;
	}
	if (change && nextState === CANCELLED_STATE) {
		const confirmed = await askConfirmation({
			title: translate("Cancel the change request?"),
			message: translate("Cancel \"{0}\"? Its task stays in the project.", [request.subject]),
			confirmLabel: translate("Cancel change request"),
			tone: "red",
		});
		if (!confirmed) return;
	}

	const shownState = change ? CHANGE_REQUEST_STATE_ALIASES[nextState] || nextState : nextState;
	pendingStates.value = { ...pendingStates.value, [request.name]: shownState };
	await (change ? applyChangeRequestAction : runWorkflowAction)(request, action);
	clearPending(request.name);
}

function clearPending(name) {
	const next = { ...pendingStates.value };
	delete next[name];
	pendingStates.value = next;
}

function moveRequest(request, targetState) {
	const move = (isChangeView.value ? getChangeRequestMoves : getRequestMoves)(request)[targetState];
	if (!move) return;
	if (move.type === "convert") {
		convertRequest(request);
	} else {
		applyAction(request, move.action, move.nextState);
	}
}

function handleDrawerAction(action) {
	if (selectedRequest.value) applyAction(selectedRequest.value, action.action, action.next_state);
}

// --- New request ------------------------------------------------------------

const showCreateModal = ref(false);

function openCreateModal() {
	if (hasCustomer.value) showCreateModal.value = true;
}

// The modal reports the creation itself; the new request opens in the drawer.
function handleCreated(result) {
	showCreateModal.value = false;
	setView("customer");
	notifyRequestsChanged(props.projectId);
	fetchRequests();
	if (result?.name) selectedName.value = result.name;
}

// --- Window behaviour -------------------------------------------------------

function refresh() {
	now.value = new Date();
	fetchRequests();
}

// Coming back to the window refetches, in case another user changed requests.
function handleFocus() {
	if (loading.value) return;
	if (!lastLoadedAt.value || Date.now() - lastLoadedAt.value.getTime() > 15000) refresh();
}

function isTyping(target) {
	return (
		target instanceof HTMLElement &&
		(target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName))
	);
}

function handleKeydown(event) {
	if (event.ctrlKey || event.metaKey || event.altKey) return;
	if (showCreateModal.value || confirmation.value || selectedName.value) return;
	if (isTyping(event.target)) return;
	if (event.key === "/") {
		event.preventDefault();
		searchInput.value?.focus();
	} else if ((event.key === "n" || event.key === "N") && !isChangeView.value) {
		event.preventDefault();
		openCreateModal();
	}
}

// Captured on document so Escape closes the dialog and not the drawer below it.
function handleConfirmationEscape(event) {
	if (event.key !== "Escape" || !confirmation.value) return;
	event.stopPropagation();
	settleConfirmation(false);
}

onMounted(() => {
	window.addEventListener("keydown", handleKeydown);
	window.addEventListener("focus", handleFocus);
	document.addEventListener("keydown", handleConfirmationEscape, true);
});

onUnmounted(() => {
	window.removeEventListener("keydown", handleKeydown);
	window.removeEventListener("focus", handleFocus);
	document.removeEventListener("keydown", handleConfirmationEscape, true);
});
</script>

<template>
	<!-- Fixed to the window: the board is meant to fill its own popup window. -->
	<div class="fixed inset-0 z-30 flex flex-col overflow-hidden bg-gray-50 text-gray-900">
		<header class="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-b border-gray-200 bg-white px-4 py-3 sm:px-6">
			<div class="flex min-w-0 items-center gap-3">
				<div class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
					<SquareKanban class="h-5 w-5" />
				</div>
				<div class="min-w-0">
					<div class="flex flex-wrap items-baseline gap-x-2.5">
						<h1 class="text-lg font-semibold">{{ translate("Requests board") }}</h1>
						<span class="truncate text-sm text-gray-600">{{ projectId }} · {{ projectLabel }}</span>
					</div>
					<div class="mt-0.5 text-xs text-gray-600">
						<span v-if="project?.customer">{{ translate("Customer") }}: {{ project.customer }} · </span>
						<span v-if="loading" class="text-gray-500">{{ translate("Loading") }}...</span>
						<span v-else-if="syncedAt" class="text-green-700">● {{ translate("Updated at {0}", [syncedAt]) }}</span>
					</div>
				</div>
			</div>
			<div class="flex flex-wrap items-center gap-2">
				<button
					type="button"
					class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
					:title="translate('Refresh')"
					:aria-label="translate('Refresh')"
					:disabled="loading"
					@click="refresh"
				>
					<RefreshCw :class="['h-4 w-4', { 'animate-spin': loading }]" />
				</button>
				<a
					:href="projectUrl"
					target="_blank"
					class="inline-flex h-9 items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
				>
					<ExternalLink class="h-4 w-4" />
					{{ translate("Open project") }}
				</a>
				<button
					type="button"
					:disabled="!hasCustomer"
					:title="hasCustomer ? translate('New request (N)') : translate('Project must have a customer')"
					class="inline-flex h-9 items-center gap-1.5 rounded-lg bg-gray-900 px-3.5 text-sm font-medium text-white hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
					@click="openCreateModal"
				>
					<Plus class="h-4 w-4" />
					{{ translate("New Customer Request") }}
				</button>
			</div>
		</header>

		<div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-gray-200 bg-white px-4 py-2.5 sm:px-6">
			<div class="flex flex-wrap items-center gap-2">
				<div role="tablist" :aria-label="translate('Requests board')" class="inline-flex gap-0.5 rounded-lg bg-gray-900/5 p-0.5">
					<button
						v-for="view in VIEW_TABS"
						:key="view.key"
						type="button"
						role="tab"
						:aria-selected="filters.view === view.key"
						:class="[
							'inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-sm',
							filters.view === view.key
								? 'bg-gray-900 font-semibold text-white'
								: 'font-medium text-gray-700 hover:bg-white',
						]"
						@click="setView(view.key)"
					>
						{{ translate(view.label) }}
						<span
							:class="[
								'rounded-full px-1.5 text-xs tabular-nums',
								filters.view === view.key ? 'bg-white/20' : 'bg-gray-200',
							]"
						>
							{{ openCounts[view.key] }}
						</span>
					</button>
				</div>
				<label class="relative flex items-center">
					<Search class="pointer-events-none absolute left-2.5 h-4 w-4 text-gray-500" />
					<input
						ref="searchInput"
						v-model="filters.q"
						type="search"
						:aria-label="translate('Search requests...')"
						:placeholder="translate('Search requests...') + ' (/)'"
						class="h-9 w-72 max-w-[70vw] rounded-lg border border-gray-300 bg-gray-50 pl-8 pr-3 text-sm focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-100"
					/>
				</label>
				<div
					v-if="!isChangeView"
					role="group"
					:aria-label="translate('Assigned To')"
					class="inline-flex gap-0.5 rounded-lg bg-gray-100 p-0.5"
				>
					<button
						v-for="option in ASSIGNMENT_FILTERS"
						:key="option.key"
						type="button"
						:aria-pressed="filters.assigned === option.key"
						:class="[
							'h-8 rounded-md px-3 text-sm',
							filters.assigned === option.key
								? 'bg-white font-semibold text-gray-900 shadow-sm'
								: 'font-medium text-gray-600 hover:text-gray-900',
						]"
						@click="filters.assigned = option.key"
					>
						{{ translate(option.label) }}
					</button>
				</div>
				<select
					v-if="!isChangeView"
					v-model="filters.source"
					:aria-label="translate('Source')"
					class="h-9 rounded-lg border border-gray-300 bg-white px-2.5 text-sm text-gray-800"
				>
					<option value="">{{ translate("All sources") }}</option>
					<option v-for="source in REQUEST_SOURCES" :key="source" :value="source">
						{{ translate(source) }}
					</option>
				</select>
				<label class="relative flex items-center">
					<CalendarDays class="pointer-events-none absolute left-2.5 h-4 w-4 text-gray-500" />
					<select
						v-model="filters.period"
						:aria-label="isChangeView ? translate('Created On') : translate('Request Date')"
						class="h-9 rounded-lg border border-gray-300 bg-white pl-8 pr-2.5 text-sm text-gray-800"
					>
						<option v-for="period in PERIODS" :key="period.value" :value="period.value">
							{{ translate(period.label) }}
						</option>
					</select>
				</label>
			</div>
			<div class="flex flex-wrap items-center gap-4 text-sm text-gray-700">
				<span><b class="font-semibold text-gray-900">{{ summary.count }}</b> {{ translate("active") }}</span>
				<span v-if="summary.hours">
					<b class="font-semibold text-gray-900">{{ formatNumber(summary.hours) }}</b>
					{{ isChangeView ? translate("h approved") : translate("h estimated") }}
				</span>
				<span v-if="summary.amounts" class="font-semibold text-gray-900">{{ summary.amounts }}</span>
			</div>
		</div>

		<div
			v-if="!available"
			class="m-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
		>
			{{ translate("You do not have access to the customer requests of this project.") }}
		</div>
		<template v-else>
			<div
				v-if="error"
				class="mx-4 mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 sm:mx-6"
			>
				{{ error }}
			</div>
			<main class="min-h-0 flex-1">
				<RequestsKanban
					:key="filters.view"
					:columns="columns"
					:busy-request="busyRequest"
					:can-add="!isChangeView && hasCustomer"
					:now="now"
					:get-moves="isChangeView ? getChangeRequestMoves : getRequestMoves"
					:card-component="isChangeView ? ChangeRequestCard : RequestBoardCard"
					@open="openRequest"
					@move="moveRequest"
					@take="takeRequest"
					@convert="convertRequest"
					@add="openCreateModal"
				/>
			</main>
		</template>

		<ChangeRequestDrawer
			v-if="selectedRequest && isChangeView"
			:request="selectedRequest"
			:project-name="projectId"
			:busy="busyRequest === selectedRequest.name"
			@close="selectedName = ''"
			@action="handleDrawerAction"
			@open-customer-request="openLinked('customer', $event)"
		/>
		<RequestDetailDrawer
			v-else-if="selectedRequest"
			:request="selectedRequest"
			:project-name="projectId"
			:customer="project?.customer || ''"
			:busy="busyRequest === selectedRequest.name"
			:current-user="currentUser"
			:save-analysis="saveAnalysis"
			@close="selectedName = ''"
			@action="handleDrawerAction"
			@convert="convertRequest(selectedRequest)"
			@take="takeRequest(selectedRequest)"
			@release="releaseRequest(selectedRequest)"
			@open-change-request="openLinked('change', $event)"
		/>

		<CustomerRequestModal
			:open="showCreateModal"
			:project="projectId"
			:project-label="projectLabel"
			:customer="project?.customer || ''"
			@close="showCreateModal = false"
			@created="handleCreated"
		/>

		<div
			v-if="confirmation"
			class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 p-4"
			@click.self="settleConfirmation(false)"
		>
			<div
				role="dialog"
				aria-modal="true"
				:aria-label="confirmation.title"
				class="flex w-[420px] max-w-full flex-col gap-3 rounded-xl bg-white p-5 shadow-2xl"
			>
				<h2 class="text-base font-semibold">{{ confirmation.title }}</h2>
				<p class="text-sm leading-relaxed text-gray-700">{{ confirmation.message }}</p>
				<div class="mt-2 flex justify-end gap-2">
					<button
						type="button"
						class="h-9 rounded-lg border border-gray-200 bg-white px-3.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
						@click="settleConfirmation(false)"
					>
						{{ translate("Cancel") }}
					</button>
					<button
						type="button"
						:class="[
							'h-9 rounded-lg px-3.5 text-sm font-medium text-white',
							confirmation.tone === 'red' ? 'bg-red-700 hover:bg-red-800' : 'bg-violet-700 hover:bg-violet-800',
						]"
						@click="settleConfirmation(true)"
					>
						{{ confirmation.confirmLabel }}
					</button>
				</div>
			</div>
		</div>

		<div class="pointer-events-none fixed bottom-5 left-1/2 z-[60] flex -translate-x-1/2 flex-col items-center gap-2">
			<div
				v-for="toast in toasts"
				:key="toast.id"
				role="status"
				:class="[
					'rounded-lg px-4 py-2.5 text-sm shadow-lg',
					toast.kind === 'error' ? 'bg-red-700 text-white' : 'bg-gray-900 text-white',
				]"
			>
				{{ toast.message }}
			</div>
		</div>
	</div>
</template>
