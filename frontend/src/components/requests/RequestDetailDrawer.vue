<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import dayjs from "dayjs";
import { TextEditor } from "frappe-ui";
import {
	Check,
	ExternalLink,
	GitPullRequestArrow,
	Hand,
	RefreshCw,
	Save,
	UserMinus,
	X,
} from "lucide-vue-next";
import { translate } from "../../utils/translation";
import {
	CUSTOMER_REQUEST_PIPELINE,
	REJECTED_STATE,
	apiGet,
	deskUrl,
	formatNumber,
	getRequestStateClass,
	htmlToText,
	isAssignedTo,
} from "../../utils/customerRequests";

const props = defineProps({
	request: {
		type: Object,
		required: true,
	},
	projectName: {
		type: String,
		required: true,
	},
	customer: {
		type: String,
		default: "",
	},
	busy: {
		type: Boolean,
		default: false,
	},
	currentUser: {
		type: String,
		default: "",
	},
	// async (request, values) => boolean
	saveAnalysis: {
		type: Function,
		required: true,
	},
});

const emit = defineEmits(["close", "action", "convert", "take", "release", "open-change-request"]);

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;

// The values the form started from: the request as last synchronised. Edits
// are measured against it, not against the request prop, which a refetch
// (from another window, say) can move under an untouched form.
const baseline = ref(formFromRequest());
const form = ref(formFromRequest());
const formError = ref("");
const saving = ref(false);
const currencyOptions = ref([]);
let optionsLoadedFor = "";

const canEdit = computed(() => Boolean(props.request.can_edit_analysis));
const isAnalysis = computed(() => props.request.workflow_state === "To Analyze");
const assignedToMe = computed(() => isAssignedTo(props.request, props.currentUser));
const assignees = computed(() =>
	(props.request.assigned_to || []).map((assignee) => assignee.full_name || assignee.user).join(", ")
);
const stateIndex = computed(() => CUSTOMER_REQUEST_PIPELINE.indexOf(props.request.workflow_state || "Draft"));
const requestDate = computed(() =>
	props.request.request_date ? dayjs(props.request.request_date).format("DD.MM.YYYY") : ""
);
const stateSince = computed(() =>
	props.request.state_changed_on ? dayjs(props.request.state_changed_on).format("DD.MM.YYYY HH:mm") : ""
);
const estimate = computed(() => {
	const parts = [];
	if (props.request.estimated_hours) parts.push(`${formatNumber(props.request.estimated_hours)} h`);
	if (props.request.estimated_amount) {
		parts.push(`${formatNumber(props.request.estimated_amount)} ${props.request.currency || ""}`.trim());
	}
	return parts.join(" · ");
});

function formFromRequest() {
	return {
		analysis: props.request.analysis || "",
		estimated_hours: props.request.estimated_hours || "",
		currency: props.request.currency || "",
		estimated_amount: props.request.estimated_amount || "",
	};
}

function formFromSavedValues(values) {
	return {
		analysis: values?.analysis || "",
		estimated_hours: values?.estimated_hours ?? "",
		currency: values?.currency || "",
		estimated_amount: values?.estimated_amount ?? "",
	};
}

function sameNumber(a, b) {
	return (Number(a) || 0) === (Number(b) || 0);
}

function sameValues(a, b) {
	return (
		(a.analysis || "") === (b.analysis || "") &&
		sameNumber(a.estimated_hours, b.estimated_hours) &&
		sameNumber(a.estimated_amount, b.estimated_amount) &&
		(a.currency || "") === (b.currency || "")
	);
}

const dirty = computed(() => canEdit.value && !sameValues(form.value, baseline.value));

function syncForm() {
	baseline.value = formFromRequest();
	form.value = formFromRequest();
}

// Another request, or the same one refetched after a change made elsewhere:
// take its values unless the user is in the middle of editing.
watch(
	() => props.request.name,
	() => {
		syncForm();
		formError.value = "";
	}
);
watch(
	() => [
		props.request.analysis,
		props.request.estimated_hours,
		props.request.currency,
		props.request.estimated_amount,
	],
	() => {
		if (!saving.value && !dirty.value) syncForm();
	}
);

watch(
	canEdit,
	(editable) => {
		if (editable) loadOptions();
	},
	{ immediate: true }
);

async function loadOptions() {
	if (optionsLoadedFor === props.projectName) return;
	optionsLoadedFor = props.projectName;
	try {
		const result = await apiGet(
			"erpnext_projekt_hub.api.project_hub.get_customer_request_dropdown_options",
			{ project: props.projectName }
		);
		currencyOptions.value = result?.currencies || [];
	} catch (err) {
		console.error("Failed to load customer request options:", err);
		optionsLoadedFor = "";
	}
}

function withCurrent(options, value) {
	if (!value || options.some((option) => option.value === value)) return options;
	return [{ value, label: value }, ...options];
}

function validate() {
	const hours = form.value.estimated_hours;
	if (hours !== "" && hours !== null && (!Number.isFinite(Number(hours)) || Number(hours) < 0)) {
		return translate("Enter a valid number of hours");
	}
	const amount = form.value.estimated_amount;
	if (amount !== "" && amount !== null && (!Number.isFinite(Number(amount)) || Number(amount) < 0)) {
		return translate("Enter a valid amount");
	}
	if (Number(amount) && !form.value.currency) {
		return translate("Currency is required when amount is provided");
	}
	return "";
}

async function save() {
	if (saving.value) return false;
	formError.value = validate();
	if (formError.value) return false;

	saving.value = true;
	try {
		const values = {
			analysis: form.value.analysis || "",
			estimated_hours: form.value.estimated_hours ?? "",
			currency: form.value.currency || "",
			estimated_amount: form.value.estimated_amount ?? "",
		};
		const savedValues = await props.saveAnalysis(props.request, values);
		if (savedValues) {
			// Edits typed while the save was on its way stay in the form, unsaved.
			const savedForm = formFromSavedValues(savedValues);
			if (sameValues(form.value, values)) {
				baseline.value = savedForm;
				form.value = savedForm;
			} else {
				baseline.value = savedForm;
			}
		}
		return Boolean(savedValues);
	} finally {
		saving.value = false;
	}
}

// An action taken with unsaved analysis saves it first: marking the request
// quoted needs the analysis and estimate on the server.
async function runAction(action) {
	if (dirty.value && !(await save())) return;
	if (dirty.value) return;
	emit("action", action);
}

function close() {
	if (dirty.value && !realWindow?.confirm(translate("Discard unsaved changes?"))) return;
	emit("close");
}

function actionClass(action) {
	if (action.next_state === REJECTED_STATE) {
		return "border border-red-300 bg-white text-red-800 hover:bg-red-50";
	}
	return "bg-gray-900 text-white hover:bg-gray-700";
}

function stepClass(index) {
	if (props.request.workflow_state === REJECTED_STATE) return "bg-gray-200";
	if (index < stateIndex.value) return "bg-green-500";
	if (index === stateIndex.value) return "bg-green-600";
	return "bg-gray-200";
}

function handleKeydown(event) {
	if (event.key === "Escape") close();
}

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => window.removeEventListener("keydown", handleKeydown));
</script>

<template>
	<div class="fixed inset-0 z-40 flex justify-end bg-gray-900/30" @click.self="close">
		<aside
			:aria-label="translate('Request details')"
			class="flex h-full w-[560px] max-w-full flex-col bg-white shadow-2xl"
		>
			<div class="flex flex-col gap-3 border-b border-gray-200 px-5 pb-4 pt-4 sm:px-6">
				<div class="flex items-center gap-2">
					<span class="font-mono text-xs text-gray-500">{{ request.name }}</span>
					<span
						:class="['rounded-full px-2 py-0.5 text-xs font-semibold', getRequestStateClass(request.workflow_state)]"
					>
						{{ translate(request.workflow_state || "Draft") }}
					</span>
					<RefreshCw v-if="busy" class="h-3.5 w-3.5 animate-spin text-gray-400" />
					<span class="flex-1"></span>
					<a
						:href="deskUrl('Customer Request', request.name)"
						target="_blank"
						rel="noopener noreferrer"
						class="inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-900"
					>
						{{ translate("Open in Desk") }}
						<ExternalLink class="h-3.5 w-3.5" />
					</a>
					<button
						type="button"
						class="rounded-md bg-gray-100 p-1.5 text-gray-600 hover:bg-gray-200"
						:aria-label="translate('Close')"
						@click="close"
					>
						<X class="h-4 w-4" />
					</button>
				</div>
				<h2 class="text-lg font-semibold leading-snug text-gray-900">{{ request.subject }}</h2>
				<ol class="grid grid-cols-5 gap-1" :aria-label="translate('Request stage')">
					<li v-for="(step, index) in CUSTOMER_REQUEST_PIPELINE" :key="step" class="flex flex-col gap-1">
						<span :class="['h-1 rounded-full', stepClass(index)]"></span>
						<span
							:class="[
								'text-[11px]',
								step === request.workflow_state ? 'font-semibold text-gray-900' : 'text-gray-500',
							]"
						>
							{{ translate(step) }}
						</span>
					</li>
				</ol>
				<div v-if="request.workflow_state === 'Rejected'" class="text-xs font-medium text-red-700">
					{{ translate("Rejected") }}
				</div>
			</div>

			<div class="flex flex-1 flex-col gap-5 overflow-y-auto px-5 py-4 text-sm sm:px-6">
				<dl class="grid grid-cols-2 gap-x-5 gap-y-3">
					<div>
						<dt class="text-xs text-gray-500">{{ translate("Customer") }}</dt>
						<dd class="mt-0.5 text-gray-900">{{ customer || "-" }}</dd>
					</div>
					<div>
						<dt class="text-xs text-gray-500">{{ translate("Requested By") }}</dt>
						<dd class="mt-0.5 text-gray-900">{{ request.requested_by_name || "-" }}</dd>
					</div>
					<div>
						<dt class="text-xs text-gray-500">{{ translate("Source") }} · {{ translate("Request Date") }}</dt>
						<dd class="mt-0.5 text-gray-900">
							{{ [request.source ? translate(request.source) : "", requestDate].filter(Boolean).join(" · ") || "-" }}
						</dd>
					</div>
					<div>
						<dt class="text-xs text-gray-500">{{ translate("Assigned To") }}</dt>
						<dd class="mt-0.5 text-gray-900">{{ assignees || "-" }}</dd>
					</div>
					<div v-if="stateSince">
						<dt class="text-xs text-gray-500">{{ translate("In State Since") }}</dt>
						<dd class="mt-0.5 text-gray-900">{{ stateSince }}</dd>
					</div>
					<div v-if="request.quotation || request.change_request">
						<dt class="text-xs text-gray-500">{{ translate("Commercial Documents") }}</dt>
						<dd class="mt-0.5 flex flex-wrap gap-2">
							<a
								v-if="request.quotation"
								:href="deskUrl('Quotation', request.quotation)"
								target="_blank"
								rel="noopener noreferrer"
								class="text-blue-700 hover:underline"
							>
								{{ request.quotation }}
							</a>
							<button
								v-if="request.change_request"
								type="button"
								class="text-violet-700 hover:underline"
								:title="translate('Show on the change requests board')"
								@click="emit('open-change-request', request.change_request)"
							>
								{{ request.change_request }}
							</button>
						</dd>
					</div>
				</dl>

				<section v-if="request.notes" class="flex flex-col gap-1">
					<h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ translate("Notes") }}</h3>
					<p class="whitespace-pre-line leading-relaxed text-gray-800">{{ htmlToText(request.notes) }}</p>
				</section>

				<section v-if="request.business_value" class="flex flex-col gap-1">
					<h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">
						{{ translate("Business Value") }}
					</h3>
					<p class="whitespace-pre-line leading-relaxed text-gray-800">
						{{ htmlToText(request.business_value) }}
					</p>
				</section>

				<!-- Analysis: editable while the request waits for analysis -->
				<section
					v-if="canEdit"
					class="flex flex-col gap-3 rounded-xl border border-gray-200 bg-gray-50 p-4"
				>
					<h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ translate("Analysis") }}</h3>
					<TextEditor
						:key="request.name"
						:content="form.analysis"
						:editable="true"
						:placeholder="() => translate('Add analysis')"
						editor-class="min-h-[120px] rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500"
						@change="(value) => (form.analysis = value)"
					/>
					<div class="grid grid-cols-3 gap-3">
						<label class="flex flex-col gap-1 text-xs text-gray-600">
							{{ translate("Estimated Hours") }}
							<input
								v-model="form.estimated_hours"
								type="number"
								min="0"
								step="0.25"
								class="h-9 rounded-md border border-gray-300 bg-white px-2.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
							/>
						</label>
						<label class="flex flex-col gap-1 text-xs text-gray-600">
							{{ translate("Estimated Amount") }}
							<input
								v-model="form.estimated_amount"
								type="number"
								min="0"
								step="0.01"
								class="h-9 rounded-md border border-gray-300 bg-white px-2.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
							/>
						</label>
						<label class="flex flex-col gap-1 text-xs text-gray-600">
							{{ translate("Currency") }}
							<select
								v-model="form.currency"
								class="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
							>
								<option value="">{{ translate("Select currency") }}</option>
								<option
									v-for="option in withCurrent(currencyOptions, form.currency)"
									:key="option.value"
									:value="option.value"
								>
									{{ option.label }}
								</option>
							</select>
						</label>
					</div>
					<p v-if="formError" class="text-xs text-red-700">{{ formError }}</p>
					<div class="flex items-center justify-end gap-2">
						<span v-if="dirty" class="text-xs text-amber-700">{{ translate("Unsaved changes") }}</span>
						<button
							type="button"
							:disabled="!dirty || saving || busy"
							class="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-800 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
							@click="save"
						>
							<Save class="h-4 w-4" />
							{{ saving ? translate("Saving...") : translate("Save") }}
						</button>
					</div>
				</section>

				<section v-else-if="request.analysis || estimate" class="flex flex-col gap-1">
					<h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ translate("Analysis") }}</h3>
					<p v-if="request.analysis" class="whitespace-pre-line leading-relaxed text-gray-800">
						{{ htmlToText(request.analysis) }}
					</p>
					<p v-if="estimate" class="font-medium text-gray-900">{{ estimate }}</p>
				</section>
			</div>

			<div class="flex flex-wrap items-center gap-2 border-t border-gray-200 px-5 py-3 sm:px-6">
				<button
					v-for="action in request.actions || []"
					:key="action.action"
					type="button"
					:disabled="busy || saving"
					:title="translate('Move to: {0}', [translate(action.next_state)])"
					:class="[
						'inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50',
						actionClass(action),
					]"
					@click="runAction(action)"
				>
					<X v-if="action.next_state === 'Rejected'" class="h-4 w-4" />
					<Check v-else class="h-4 w-4" />
					{{ translate(action.action) }}
				</button>
				<button
					v-if="request.can_create_change_request"
					type="button"
					:disabled="busy || saving"
					class="inline-flex items-center gap-1.5 rounded-md bg-violet-700 px-3 py-2 text-sm font-medium text-white hover:bg-violet-800 disabled:cursor-not-allowed disabled:opacity-50"
					@click="emit('convert')"
				>
					<GitPullRequestArrow class="h-4 w-4" />
					{{ translate("Create Change Request") }}
				</button>
				<template v-if="isAnalysis">
					<button
						v-if="!assignedToMe"
						type="button"
						:disabled="busy || saving"
						class="inline-flex items-center gap-1.5 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-800 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
						@click="emit('take')"
					>
						<Hand class="h-4 w-4" />
						{{ translate("Take for analysis") }}
					</button>
					<button
						v-else
						type="button"
						:disabled="busy || saving"
						class="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
						@click="emit('release')"
					>
						<UserMinus class="h-4 w-4" />
						{{ translate("Release") }}
					</button>
				</template>
			</div>
		</aside>
	</div>
</template>
