<script setup>
import { onUnmounted, ref, watch } from "vue";
import dayjs from "dayjs";
import { X } from "lucide-vue-next";
import { TextEditor } from "frappe-ui";
import { translate } from "../../utils/translation";
import { REQUEST_SOURCES, apiGet, apiPost, decodeApiError } from "../../utils/customerRequests";

const props = defineProps({
	open: {
		type: Boolean,
		default: false,
	},
	// The request is created for this project.
	project: {
		type: String,
		default: "",
	},
	projectLabel: {
		type: String,
		default: "",
	},
	customer: {
		type: String,
		default: "",
	},
	// Prefill for fields typed before opening the full form (quick add).
	initialSubject: {
		type: String,
		default: "",
	},
	initialSource: {
		type: String,
		default: "",
	},
});

const emit = defineEmits(["close", "created"]);

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;

const creatingRequest = ref(false);
const submitError = ref("");
const formErrors = ref({});
const requestedByOptions = ref([]);
const requestedByLoading = ref(false);
const currencyOptions = ref([]);
const quotationOptions = ref([]);
const loadingDropdownOptions = ref(false);
const createForm = ref(emptyForm());
// Bumped on every open and close: a dropdown response that arrives for an
// older generation belongs to an earlier opening (maybe of another project).
let loadGeneration = 0;

function emptyForm() {
	return {
		project: props.project || "",
		subject: props.initialSubject || "",
		request_date: dayjs().format("YYYY-MM-DD"),
		source: props.initialSource || "",
		requested_by: "",
		notes: "",
		business_value: "",
		analysis: "",
		estimated_hours: "",
		currency: "",
		estimated_amount: "",
		quotation: "",
	};
}

function showAlert(message, indicator = "blue") {
	if (realWindow?.frappe?.show_alert) {
		realWindow.frappe.show_alert({ message, indicator });
	}
}

function resetCreateForm() {
	createForm.value = emptyForm();
	formErrors.value = {};
	submitError.value = "";
	requestedByOptions.value = [];
	currencyOptions.value = [];
	quotationOptions.value = [];
}

function closeCreateModal() {
	if (creatingRequest.value) return;
	emit("close");
}

function setField(field, value) {
	createForm.value[field] = value ?? "";
}

async function loadRequestedByOptions(query = "") {
	if (!createForm.value.project) {
		requestedByOptions.value = [];
		return;
	}

	const generation = loadGeneration;
	requestedByLoading.value = true;
	try {
		const result = await apiGet("erpnext_projekt_hub.api.project_hub.search_requested_by", {
			project: createForm.value.project,
			txt: query,
		});
		if (generation !== loadGeneration) return;
		requestedByOptions.value = Array.isArray(result) ? result : [];
	} catch (err) {
		if (generation !== loadGeneration) return;
		console.error("Failed to fetch requested by options:", err);
		requestedByOptions.value = [];
	} finally {
		if (generation === loadGeneration) requestedByLoading.value = false;
	}
}

async function loadDropdownOptions() {
	if (!createForm.value.project) {
		currencyOptions.value = [];
		quotationOptions.value = [];
		return;
	}

	const generation = loadGeneration;
	loadingDropdownOptions.value = true;
	try {
		const result = await apiGet(
			"erpnext_projekt_hub.api.project_hub.get_customer_request_dropdown_options",
			{ project: createForm.value.project }
		);
		if (generation !== loadGeneration) return;
		currencyOptions.value = result?.currencies || [];
		quotationOptions.value = result?.quotations || [];
	} catch (err) {
		if (generation !== loadGeneration) return;
		console.error("Failed to fetch customer request dropdown options:", err);
		currencyOptions.value = [];
		quotationOptions.value = [];
	} finally {
		if (generation === loadGeneration) loadingDropdownOptions.value = false;
	}
}

function validateCreateForm() {
	const nextErrors = {};
	const subject = createForm.value.subject.trim();

	if (!subject) {
		nextErrors.subject = translate("Subject is required");
	}

	if (createForm.value.estimated_hours !== "" && createForm.value.estimated_hours !== null) {
		const hours = Number(createForm.value.estimated_hours);
		if (!Number.isFinite(hours) || hours < 0) {
			nextErrors.estimated_hours = translate("Enter a valid number of hours");
		}
	}

	if (createForm.value.estimated_amount !== "" && createForm.value.estimated_amount !== null) {
		const amount = Number(createForm.value.estimated_amount);
		if (!Number.isFinite(amount) || amount < 0) {
			nextErrors.estimated_amount = translate("Enter a valid amount");
		}
	}

	if ((createForm.value.estimated_amount !== "" && createForm.value.estimated_amount !== null) && !createForm.value.currency) {
		nextErrors.currency = translate("Currency is required when amount is provided");
	}

	formErrors.value = nextErrors;
	return Object.keys(nextErrors).length === 0;
}

async function submitCustomerRequest() {
	if (!createForm.value.project) {
		submitError.value = translate("Project is required");
		return;
	}

	if (!validateCreateForm()) {
		submitError.value = translate("Please fix the highlighted fields");
		showAlert(submitError.value, "red");
		return;
	}

	creatingRequest.value = true;
	submitError.value = "";
	try {
		const result = await apiPost("erpnext_projekt_hub.api.project_hub.create_customer_request", {
			project: createForm.value.project,
			subject: createForm.value.subject.trim(),
			request_date: createForm.value.request_date,
			source: createForm.value.source,
			requested_by: createForm.value.requested_by,
			notes: createForm.value.notes,
			business_value: createForm.value.business_value,
			analysis: createForm.value.analysis,
			estimated_hours: createForm.value.estimated_hours,
			currency: createForm.value.currency,
			estimated_amount: createForm.value.estimated_amount,
			quotation: createForm.value.quotation,
		});
		showAlert(translate("Customer request created"), "green");
		emit("created", result);
	} catch (err) {
		console.error("Failed to create customer request:", err);
		submitError.value = decodeApiError(err, translate("Customer request could not be created"));
		showAlert(submitError.value, "red");
	} finally {
		creatingRequest.value = false;
	}
}

// Captured on document so Escape closes only the modal, not the panels behind
// it that listen on window.
function handleEscape(event) {
	if (event.key !== "Escape") return;
	event.stopPropagation();
	closeCreateModal();
}

watch(
	() => props.open,
	(open) => {
		loadGeneration += 1;
		if (!open) {
			document.removeEventListener("keydown", handleEscape, true);
			return;
		}
		document.addEventListener("keydown", handleEscape, true);
		resetCreateForm();
		void loadRequestedByOptions("");
		void loadDropdownOptions();
	},
	{ immediate: true }
);

onUnmounted(() => {
	document.removeEventListener("keydown", handleEscape, true);
});
</script>

<template>
	<Teleport to="body">
		<div
			v-if="open"
			class="fixed inset-0 z-50 overflow-y-auto bg-gray-900/50 px-4 py-6"
			@click.self="closeCreateModal"
		>
			<div class="mx-auto flex w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl">
				<div class="flex items-center justify-between border-b border-gray-100 px-5 py-4">
					<div>
						<h3 class="text-lg font-semibold text-gray-900">
							{{ translate("New Customer Request") }}
						</h3>
						<p class="text-sm text-gray-500">
							{{ projectLabel || createForm.project }}
							<span v-if="customer"> · {{ customer }}</span>
						</p>
					</div>
					<button
						type="button"
						class="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
						:disabled="creatingRequest"
						@click="closeCreateModal"
					>
						<X class="h-5 w-5" />
					</button>
				</div>

				<div class="flex min-h-0 flex-1 flex-col">
					<div class="min-h-0 flex-1 space-y-5 overflow-y-auto px-5 py-5">
						<div
							v-if="submitError"
							class="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
						>
							{{ submitError }}
						</div>

						<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
							<div class="md:col-span-2">
								<label class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Subject") }}
								</label>
								<input
									v-model="createForm.subject"
									type="text"
									class="h-10 w-full rounded-md border px-3 text-sm text-gray-900 focus:outline-none focus:ring-2"
									:class="formErrors.subject
										? 'border-red-300 focus:border-red-500 focus:ring-red-100'
										: 'border-gray-300 focus:border-emerald-500 focus:ring-emerald-100'"
									:placeholder="translate('Describe the request')"
								/>
								<p v-if="formErrors.subject" class="mt-1 text-xs text-red-600">
									{{ formErrors.subject }}
								</p>
							</div>

							<div>
								<label class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Request Date") }}
								</label>
								<input
									v-model="createForm.request_date"
									type="date"
									class="h-10 w-full rounded-md border border-gray-300 px-3 text-sm text-gray-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100"
								/>
							</div>

							<div>
								<label class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Source") }}
								</label>
								<select
									v-model="createForm.source"
									class="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100"
								>
									<option value="">{{ translate("Select source") }}</option>
									<option v-for="source in REQUEST_SOURCES" :key="source" :value="source">
										{{ translate(source) }}
									</option>
								</select>
							</div>

							<div class="md:col-span-2">
								<label class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Requested By") }}
								</label>
								<select
									v-model="createForm.requested_by"
									class="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100"
									:disabled="requestedByLoading"
								>
									<option value="">
										{{ requestedByLoading ? translate("Loading...") : translate("Select employee") }}
									</option>
									<option
										v-for="employee in requestedByOptions"
										:key="employee.value"
										:value="employee.value"
									>
										{{ employee.label }}
										{{ employee.description ? `(${employee.description})` : "" }}
									</option>
								</select>
							</div>

							<div class="md:col-span-2">
								<div class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Notes") }}
								</div>
								<TextEditor
									:content="createForm.notes"
									:editable="true"
									:placeholder="() => translate('Add request details')"
									editor-class="min-h-[112px] rounded-md border border-gray-300 bg-white px-4 py-3 text-sm focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500"
									@change="(value) => setField('notes', value)"
								/>
							</div>

							<div class="md:col-span-2">
								<div class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Business Value") }}
								</div>
								<TextEditor
									:content="createForm.business_value"
									:editable="true"
									:placeholder="() => translate('Why this request matters')"
									editor-class="min-h-[112px] rounded-md border border-gray-300 bg-white px-4 py-3 text-sm focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500"
									@change="(value) => setField('business_value', value)"
								/>
							</div>

							<div class="md:col-span-2">
								<div class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Analysis") }}
								</div>
								<TextEditor
									:content="createForm.analysis"
									:editable="false"
									:placeholder="() => translate('Add analysis')"
									editor-class="min-h-[112px] rounded-md border border-gray-300 bg-gray-50 px-4 py-3 text-sm text-gray-500"
									@change="(value) => setField('analysis', value)"
								/>
							</div>

							<div>
								<label class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Estimated Hours") }}
								</label>
								<input
									v-model.number="createForm.estimated_hours"
									type="number"
									min="0"
									step="0.25"
									readonly
									class="h-10 w-full cursor-not-allowed rounded-md border border-gray-300 bg-gray-50 px-3 text-sm text-gray-500 focus:outline-none focus:ring-2"
									:class="formErrors.estimated_hours
										? 'border-red-300 focus:border-red-500 focus:ring-red-100'
										: 'border-gray-300 focus:border-emerald-500 focus:ring-emerald-100'"
								/>
								<p v-if="formErrors.estimated_hours" class="mt-1 text-xs text-red-600">
									{{ formErrors.estimated_hours }}
								</p>
							</div>

							<div>
								<label class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Currency") }}
								</label>
								<select
									v-model="createForm.currency"
									class="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100"
									:disabled="loadingDropdownOptions"
								>
									<option value="">
										{{ loadingDropdownOptions ? translate("Loading...") : translate("Select currency") }}
									</option>
									<option
										v-for="currency in currencyOptions"
										:key="currency.value"
										:value="currency.value"
									>
										{{ currency.label }}
									</option>
								</select>
								<p v-if="formErrors.currency" class="mt-1 text-xs text-red-600">
									{{ formErrors.currency }}
								</p>
							</div>

							<div>
								<label class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Estimated Amount") }}
								</label>
								<input
									v-model.number="createForm.estimated_amount"
									type="number"
									min="0"
									step="0.01"
									readonly
									class="h-10 w-full cursor-not-allowed rounded-md border border-gray-300 bg-gray-50 px-3 text-sm text-gray-500 focus:outline-none focus:ring-2"
									:class="formErrors.estimated_amount
										? 'border-red-300 focus:border-red-500 focus:ring-red-100'
										: 'border-gray-300 focus:border-emerald-500 focus:ring-emerald-100'"
								/>
								<p v-if="formErrors.estimated_amount" class="mt-1 text-xs text-red-600">
									{{ formErrors.estimated_amount }}
								</p>
							</div>

							<div>
								<label class="mb-1 block text-sm font-medium text-gray-700">
									{{ translate("Quotation") }}
								</label>
								<select
									v-model="createForm.quotation"
									class="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100"
									:disabled="loadingDropdownOptions"
								>
									<option value="">
										{{ loadingDropdownOptions ? translate("Loading...") : translate("Select quotation") }}
									</option>
									<option
										v-for="quotation in quotationOptions"
										:key="quotation.value"
										:value="quotation.value"
									>
										{{ quotation.label }}
										{{ quotation.description ? `(${quotation.description})` : "" }}
									</option>
								</select>
							</div>
						</div>
					</div>

					<div class="sticky bottom-0 z-10 flex flex-nowrap items-center justify-between gap-3 overflow-x-auto border-t border-gray-100 bg-white px-5 py-4 shadow-[0_-8px_20px_rgba(15,23,42,0.06)]">
						<button
							type="button"
							class="inline-flex h-10 w-[120px] flex-none items-center justify-center rounded-md border border-gray-300 bg-white px-4 text-sm font-medium text-gray-700 hover:bg-gray-50"
							:disabled="creatingRequest"
							@click="closeCreateModal"
						>
							{{ translate("Cancel") }}
						</button>
						<button
							type="button"
							class="inline-flex h-10 w-[180px] flex-none items-center justify-center rounded-md px-4 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-60"
							style="background-color: #000000; border-color: #000000; color: #ffffff;"
							:disabled="creatingRequest"
							@click="submitCustomerRequest"
						>
							{{ creatingRequest ? translate("Creating...") : translate("Zatwierdź") }}
						</button>
					</div>
				</div>
			</div>
		</div>
	</Teleport>
</template>
