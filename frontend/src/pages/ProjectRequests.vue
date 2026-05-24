<script setup>
import { computed, onMounted, ref, watch } from "vue";
import dayjs from "dayjs";
import { ClipboardList, ExternalLink, Plus, RefreshCw, X } from "lucide-vue-next";
import { TextEditor } from "frappe-ui";
import OutlinerNav from "../components/OutlinerNav.vue";
import { translate } from "../utils/translation";

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;

const projects = ref([]);
const selectedProject = ref("");
const projectInfo = ref(null);
const customerRequests = ref([]);
const changeRequests = ref([]);
const loadingProjects = ref(true);
const loadingRequests = ref(false);
const creatingRequest = ref(false);
const error = ref("");
const showCreateModal = ref(false);
const submitError = ref("");
const formErrors = ref({});
const requestedByOptions = ref([]);
const requestedByLoading = ref(false);
const currencyOptions = ref([]);
const quotationOptions = ref([]);
const loadingDropdownOptions = ref(false);
const createForm = ref({
	project: "",
	subject: "",
	request_date: dayjs().format("YYYY-MM-DD"),
	source: "",
	requested_by: "",
	notes: "",
	business_value: "",
	analysis: "",
	estimated_hours: "",
	currency: "",
	estimated_amount: "",
	quotation: "",
});

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

async function apiPost(method, payload = {}) {
	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: {
			"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
			"X-Frappe-CSRF-Token": getCsrfToken(),
		},
		body: new URLSearchParams(payload),
	});
	const data = await response.json();
	if (!response.ok || data.exc) {
		throw new Error(data.exception || data._server_messages || "API Error");
	}
	return data.message;
}

function showAlert(message, indicator = "blue") {
	if (realWindow?.frappe?.show_alert) {
		realWindow.frappe.show_alert({ message, indicator });
	}
}

function stripHtml(html) {
	if (!html) return "";
	return String(html).replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function decodeApiError(error, fallback) {
	const raw = error?.message || "";
	if (!raw) return fallback;

	try {
		const parsed = JSON.parse(raw);
		if (Array.isArray(parsed)) {
			const messages = parsed
				.map((entry) => {
					try {
						const decoded = JSON.parse(entry);
						return decoded.message || decoded.title || entry;
					} catch {
						return entry;
					}
				})
				.filter(Boolean);
			if (messages.length > 0) {
				return messages.join(" ");
			}
		}
	} catch {
		// fall back to raw message
	}

	return raw.replace(/^Error:\s*/i, "") || fallback;
}

function resetCreateForm() {
	createForm.value = {
		project: selectedProject.value || "",
		subject: "",
		request_date: dayjs().format("YYYY-MM-DD"),
		source: "",
		requested_by: "",
		notes: "",
		business_value: "",
		analysis: "",
		estimated_hours: "",
		currency: "",
		estimated_amount: "",
		quotation: "",
	};
	formErrors.value = {};
	submitError.value = "";
	requestedByOptions.value = [];
	currencyOptions.value = [];
	quotationOptions.value = [];
}

function handleCreateProjectChange() {
	createForm.value.requested_by = "";
	createForm.value.currency = "";
	createForm.value.quotation = "";
	void loadRequestedByOptions("");
	void loadDropdownOptions();
}

function openCreateModal() {
	resetCreateForm();
	showCreateModal.value = true;
	void loadRequestedByOptions("");
	void loadDropdownOptions();
}

function closeCreateModal() {
	if (creatingRequest.value) return;
	showCreateModal.value = false;
}

function setField(field, value) {
	createForm.value[field] = value ?? "";
}

async function loadRequestedByOptions(query = "") {
	if (!createForm.value.project) {
		requestedByOptions.value = [];
		return;
	}

	requestedByLoading.value = true;
	try {
		const result = await apiGet("erpnext_projekt_hub.api.project_hub.search_requested_by", {
			project: createForm.value.project,
			txt: query,
		});
		requestedByOptions.value = Array.isArray(result) ? result : [];
	} catch (err) {
		console.error("Failed to fetch requested by options:", err);
		requestedByOptions.value = [];
	} finally {
		requestedByLoading.value = false;
	}
}

async function loadDropdownOptions() {
	if (!createForm.value.project) {
		currencyOptions.value = [];
		quotationOptions.value = [];
		return;
	}

	loadingDropdownOptions.value = true;
	try {
		const result = await apiGet(
			"erpnext_projekt_hub.api.project_hub.get_customer_request_dropdown_options",
			{ project: createForm.value.project }
		);
		currencyOptions.value = result?.currencies || [];
		quotationOptions.value = result?.quotations || [];
	} catch (err) {
		console.error("Failed to fetch customer request dropdown options:", err);
		currencyOptions.value = [];
		quotationOptions.value = [];
	} finally {
		loadingDropdownOptions.value = false;
	}
}

function validateCreateForm() {
	const nextErrors = {};
	if (!createForm.value.project) {
		nextErrors.project = translate("Project is required");
	}
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

async function submitCustomerRequest() {
	if (!createForm.value.project) {
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
		await apiPost("erpnext_projekt_hub.api.project_hub.create_customer_request", {
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
		showCreateModal.value = false;
		showAlert(translate("Customer request created"), "green");
		await fetchRequests();
	} catch (err) {
		console.error("Failed to create customer request:", err);
		submitError.value = decodeApiError(err, translate("Customer request could not be created"));
		showAlert(submitError.value, "red");
	} finally {
		creatingRequest.value = false;
	}
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
					<button
						type="button"
						class="inline-flex h-10 min-w-[240px] items-center justify-center gap-2 rounded-md border px-4 text-sm font-semibold shadow-sm transition-all focus:outline-none focus:ring-2 disabled:cursor-not-allowed"
						:style="{
							backgroundColor: !selectedProject || loadingRequests ? '#cbd5e1' : '#0f172a',
							borderColor: !selectedProject || loadingRequests ? '#cbd5e1' : '#0f172a',
							color: '#ffffff',
						}"
						:disabled="!selectedProject || loadingRequests"
						@click="openCreateModal"
					>
						<Plus class="h-4 w-4" />
						{{ translate("Create Customer Request") }}
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

		<div
			v-if="showCreateModal"
			class="fixed inset-0 z-30 overflow-y-auto bg-slate-900/50 px-4 py-6"
			@click.self="closeCreateModal"
		>
			<div class="mx-auto flex w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl">
				<div class="flex items-center justify-between border-b border-gray-100 px-5 py-4">
					<div>
						<h3 class="text-lg font-semibold text-gray-900">
							{{ translate("New Customer Request") }}
						</h3>
						<p class="text-sm text-gray-500">
							{{ projectInfo?.project_name || selectedProject }}
							<span v-if="projectInfo?.customer"> · {{ projectInfo.customer }}</span>
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
									{{ translate("Project") }}
								</label>
								<select
									v-model="createForm.project"
									class="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100"
									@change="handleCreateProjectChange"
								>
									<option value="">{{ translate("Select project") }}</option>
									<option v-for="project in projects" :key="project.name" :value="project.name">
										{{ project.project_name || project.name }}
									</option>
								</select>
								<p v-if="formErrors.project" class="mt-1 text-xs text-red-600">
									{{ formErrors.project }}
								</p>
							</div>

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
									<option value="Meeting">{{ translate("Meeting") }}</option>
									<option value="Email">{{ translate("Email") }}</option>
									<option value="Call">{{ translate("Call") }}</option>
									<option value="Loop">{{ translate("Loop") }}</option>
									<option value="Other">{{ translate("Other") }}</option>
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
	</div>
</template>
