<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useDebounceFn } from "@vueuse/core";
import {
	Timer,
	Search,
	Filter,
	X,
	RefreshCw,
	Pencil,
	AlertCircle,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import { useMyTimeLogsStore } from "../stores/myTimeLogsStore";
import { useTaskStore } from "../stores/taskStore";
import { getRealWindow, translate } from "../utils/translation";

const store = useMyTimeLogsStore();
const taskStore = useTaskStore();
const realWindow = getRealWindow();

const showFilters = ref(false);
const searchInput = ref("");
const editModalOpen = ref(false);
const savingEdit = ref(false);
const editForm = ref({
	timelog_name: "",
	hours: "",
	activity_type: "",
	description: "",
	from_time: "",
	to_time: "",
});

const userLocale = computed(() => {
	const localeFromBoot = realWindow?.frappe?.boot?.lang;
	if (localeFromBoot) return localeFromBoot;
	if (typeof navigator !== "undefined" && navigator.language) return navigator.language;
	return "en-US";
});

const dateFormatter = computed(
	() =>
		new Intl.DateTimeFormat(userLocale.value, {
			year: "numeric",
			month: "2-digit",
			day: "2-digit",
			hour: "2-digit",
			minute: "2-digit",
		})
);

const hoursFormatter = computed(
	() => new Intl.NumberFormat(userLocale.value, { minimumFractionDigits: 0, maximumFractionDigits: 2 })
);

const statusOptions = ["Draft", "Submitted", "Billed"];

const projectOptions = computed(() => {
	const map = new Map();
	store.timelogs.forEach((log) => {
		if (log.project) {
			map.set(log.project, log.project_name || log.project);
		}
	});
	return Array.from(map.entries()).map(([value, label]) => ({ value, label }));
});

const activityTypeOptions = computed(() => {
	if (taskStore.activityTypes.length > 0) {
		return taskStore.activityTypes;
	}
	const set = new Set();
	store.timelogs.forEach((log) => {
		if (log.activity_type) {
			set.add(log.activity_type);
		}
	});
	return Array.from(set.values());
});

const totalHours = computed(() =>
	store.timelogs.reduce((sum, log) => sum + (parseFloat(log.hours) || 0), 0)
);

const draftHours = computed(() =>
	store.timelogs
		.filter((log) => isDraftLog(log))
		.reduce((sum, log) => sum + (parseFloat(log.hours) || 0), 0)
);

const draftCount = computed(() => store.timelogs.filter((log) => isDraftLog(log)).length);

const debouncedSearch = useDebounceFn((value) => {
	store.setFilter("search", value);
	store.fetchLogs();
}, 300);

watch(searchInput, (value) => {
	debouncedSearch(value);
});

onMounted(async () => {
	if (taskStore.activityTypes.length === 0) {
		taskStore.fetchActivityTypes();
	}
	await store.fetchLogs();
});

function updateFilter(key, value) {
	store.setFilter(key, value);
	store.fetchLogs();
}

function resetFilters() {
	store.resetFilters();
	searchInput.value = "";
	store.fetchLogs();
}

function toggleDraftsOnly() {
	const next = store.filters.status === "Draft" ? "" : "Draft";
	updateFilter("status", next);
}

function isDraftLog(log) {
	return log?.status === "Draft" || log?.docstatus === 0;
}

function getStatusClass(status) {
	if (status === "Submitted") return "bg-emerald-100 text-emerald-800";
	if (status === "Billed") return "bg-blue-100 text-blue-800";
	if (status === "Draft") return "bg-amber-100 text-amber-800";
	return "bg-gray-100 text-gray-700";
}

function formatDateTime(value) {
	if (!value) return "";
	const normalized = value.replace(" ", "T");
	const date = new Date(normalized);
	if (Number.isNaN(date.getTime())) return value;
	return dateFormatter.value.format(date);
}

function formatRange(log) {
	if (!log?.from_time && !log?.to_time) return "";
	if (log?.from_time && !log?.to_time) return formatDateTime(log.from_time);
	if (!log?.from_time && log?.to_time) return formatDateTime(log.to_time);
	return `${formatDateTime(log.from_time)} - ${formatDateTime(log.to_time)}`;
}

function formatHours(value) {
	const hours = parseFloat(value);
	if (Number.isNaN(hours)) return "0";
	return hoursFormatter.value.format(hours);
}

function toLocalInput(value) {
	if (!value) return "";
	const normalized = value.replace(" ", "T");
	const date = new Date(normalized);
	if (Number.isNaN(date.getTime())) return "";
	const pad = (num) => String(num).padStart(2, "0");
	return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
		date.getHours()
	)}:${pad(date.getMinutes())}`;
}

function toFrappeDateTime(value) {
	if (!value) return "";
	return `${value.replace("T", " ")}:00`;
}

function openEditModal(log) {
	if (!isDraftLog(log)) {
		showAlert(translate("Only draft time entries can be updated"), "orange");
		return;
	}
	editForm.value = {
		timelog_name: log.timelog_name,
		hours: String(log.hours ?? ""),
		activity_type: log.activity_type || "",
		description: log.description || "",
		from_time: toLocalInput(log.from_time),
		to_time: toLocalInput(log.to_time),
	};
	editModalOpen.value = true;
}

function closeEditModal() {
	editModalOpen.value = false;
	editForm.value = {
		timelog_name: "",
		hours: "",
		activity_type: "",
		description: "",
		from_time: "",
		to_time: "",
	};
}

function showAlert(message, indicator = "blue") {
	if (realWindow?.frappe) {
		realWindow.frappe.show_alert({ message, indicator });
	}
}

async function handleEditSave() {
	if (!editForm.value.timelog_name) return;
	const hoursValue = parseFloat(editForm.value.hours);
	if (!Number.isFinite(hoursValue) || hoursValue <= 0) {
		showAlert(translate("Please enter a valid number of hours"), "red");
		return;
	}
	if (!editForm.value.activity_type) {
		showAlert(translate("Please select an activity type"), "red");
		return;
	}

	savingEdit.value = true;
	try {
		const payload = {
			hours: hoursValue,
			activity_type: editForm.value.activity_type,
			description: editForm.value.description || "",
		};
		if (editForm.value.from_time) {
			payload.from_time = toFrappeDateTime(editForm.value.from_time);
		}
		if (editForm.value.to_time) {
			payload.to_time = toFrappeDateTime(editForm.value.to_time);
		}

		await store.updateTimelog(editForm.value.timelog_name, payload);
		await store.fetchLogs();
		closeEditModal();
		showAlert(translate("Time entry updated"), "green");
	} catch (error) {
		showAlert(translate("Failed to update time entry"), "red");
	} finally {
		savingEdit.value = false;
	}
}
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<Timer class="w-6 h-6 text-amber-600" />
						<h1 class="text-xl font-semibold text-gray-900">
							{{ translate("My Time Logs") }}
						</h1>
						<span
							v-if="store.total > 0"
							class="text-sm text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full"
						>
							{{ store.total }}
						</span>
					</div>
					<div class="flex items-center gap-3 sm:gap-4">
						<OutlinerNav />
						<a
							href="/app"
							class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 whitespace-nowrap"
						>
							&larr; Back to Desk
						</a>
					</div>
				</div>
			</div>
		</header>

		<div class="bg-white border-b border-gray-200 sticky top-16 z-10">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
				<div class="flex flex-col lg:flex-row lg:items-center gap-3">
					<div class="relative flex-1 max-w-lg">
						<Search
							class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
						/>
						<input
							v-model="searchInput"
							type="text"
							:placeholder="translate('Search time logs...')"
							class="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
						/>
						<button
							v-if="searchInput"
							@click="searchInput = ''"
							class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
						>
							<X class="w-4 h-4" />
						</button>
					</div>

					<div class="flex items-center gap-2">
						<button
							@click="showFilters = !showFilters"
							:class="[
								'flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors',
								showFilters || store.hasActiveFilters
									? 'bg-amber-50 border-amber-200 text-amber-700'
									: 'border-gray-300 text-gray-700 hover:bg-gray-50',
							]"
						>
							<Filter class="w-4 h-4" />
							<span class="hidden sm:inline">{{ translate("Filters") }}</span>
							<span
								v-if="store.hasActiveFilters"
								class="w-2 h-2 rounded-full bg-amber-600"
							></span>
						</button>
						<button
							@click="toggleDraftsOnly"
							:class="[
								'px-3 py-2 text-sm rounded-lg border transition-colors',
								store.filters.status === 'Draft'
									? 'bg-gray-900 border-gray-900 text-white'
									: 'border-gray-300 text-gray-700 hover:bg-gray-50',
							]"
						>
							{{ translate("Drafts only") }}
						</button>
						<button
							@click="store.fetchLogs()"
							:disabled="store.loading"
							class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
							:title="translate('Refresh')"
						>
							<RefreshCw :class="['w-4 h-4', store.loading && 'animate-spin']" />
						</button>
					</div>
				</div>

				<Transition name="slide-fade">
					<div v-if="showFilters" class="mt-4 pt-4 border-t border-gray-200">
						<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("Start date") }}
								</label>
								<input
									type="date"
									:value="store.filters.startDate"
									@change="updateFilter('startDate', $event.target.value)"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								/>
							</div>
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("End date") }}
								</label>
								<input
									type="date"
									:value="store.filters.endDate"
									@change="updateFilter('endDate', $event.target.value)"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								/>
							</div>
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("Status") }}
								</label>
								<select
									:value="store.filters.status"
									@change="updateFilter('status', $event.target.value)"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								>
									<option value="">{{ translate("All statuses") }}</option>
									<option v-for="status in statusOptions" :key="status" :value="status">
										{{ translate(status) }}
									</option>
								</select>
							</div>
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("Project") }}
								</label>
								<select
									:value="store.filters.project"
									@change="updateFilter('project', $event.target.value)"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								>
									<option value="">{{ translate("All projects") }}</option>
									<option
										v-for="project in projectOptions"
										:key="project.value"
										:value="project.value"
									>
										{{ project.label }}
									</option>
								</select>
							</div>
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("Activity type") }}
								</label>
								<select
									:value="store.filters.activityType"
									@change="updateFilter('activityType', $event.target.value)"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								>
									<option value="">{{ translate("All activities") }}</option>
									<option
										v-for="activity in activityTypeOptions"
										:key="activity"
										:value="activity"
									>
										{{ activity }}
									</option>
								</select>
							</div>
						</div>
						<div class="mt-4 flex items-center justify-between">
							<p class="text-xs text-gray-500">
								{{ translate("Filters apply to the list and totals below.") }}
							</p>
							<button
								type="button"
								@click="resetFilters"
								class="text-sm text-gray-500 hover:text-gray-700"
							>
								{{ translate("Clear filters") }}
							</button>
						</div>
					</div>
				</Transition>
			</div>
		</div>

		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<div class="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
					<p class="text-xs uppercase tracking-wide text-gray-500">
						{{ translate("Total hours") }}
					</p>
					<p class="mt-2 text-2xl font-semibold text-gray-900">
						{{ formatHours(totalHours) }} {{ translate("hrs") }}
					</p>
					<p class="text-xs text-gray-500 mt-1">
						{{ translate("Entries") }}: {{ store.timelogs.length }}
					</p>
				</div>
				<div class="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
					<p class="text-xs uppercase tracking-wide text-gray-500">
						{{ translate("Draft hours") }}
					</p>
					<p class="mt-2 text-2xl font-semibold text-gray-900">
						{{ formatHours(draftHours) }} {{ translate("hrs") }}
					</p>
					<p class="text-xs text-gray-500 mt-1">
						{{ translate("Draft entries") }}: {{ draftCount }}
					</p>
				</div>
				<div class="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
					<p class="text-xs uppercase tracking-wide text-gray-500">
						{{ translate("Filtered view") }}
					</p>
					<p class="mt-2 text-2xl font-semibold text-gray-900">
						{{ store.hasActiveFilters ? translate("Active") : translate("All") }}
					</p>
					<p class="text-xs text-gray-500 mt-1">
						{{ translate("Showing") }} {{ store.timelogs.length }}
						{{ translate("entries") }}
					</p>
				</div>
			</div>

			<div class="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
				<div
					class="hidden md:grid grid-cols-[1.6fr_1fr_1.4fr_2fr_0.6fr_0.9fr] gap-4 px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-500 uppercase"
				>
					<span>{{ translate("Task / Project") }}</span>
					<span>{{ translate("Activity") }}</span>
					<span>{{ translate("Time") }}</span>
					<span>{{ translate("Description") }}</span>
					<span>{{ translate("Hours") }}</span>
					<span class="text-right">{{ translate("Status") }}</span>
				</div>

				<div v-if="store.loading" class="py-12 text-center">
					<div class="h-8 w-8 animate-spin rounded-full border-2 border-amber-500 border-t-transparent mx-auto"></div>
				</div>

				<div
					v-else-if="store.error"
					class="py-12 text-center text-sm text-red-600 flex items-center justify-center gap-2"
				>
					<AlertCircle class="w-4 h-4" />
					<span>{{ store.error }}</span>
				</div>

				<div v-else-if="store.timelogs.length === 0" class="py-12 text-center text-sm text-gray-500">
					{{ translate("No time entries found") }}
				</div>

				<div v-else class="divide-y divide-gray-100">
					<div
						v-for="log in store.timelogs"
						:key="log.timelog_name"
						class="px-4 py-4"
					>
						<div
							class="grid gap-4 md:grid-cols-[1.6fr_1fr_1.4fr_2fr_0.6fr_0.9fr] items-start"
						>
							<div>
								<p class="text-xs text-gray-500 md:hidden">
									{{ translate("Task / Project") }}
								</p>
								<p class="text-sm font-semibold text-gray-900">
									{{ log.task_subject || log.task || translate("No task") }}
								</p>
								<p class="text-xs text-gray-500">
									{{ log.project_name || log.project || translate("No project") }}
								</p>
							</div>
							<div>
								<p class="text-xs text-gray-500 md:hidden">{{ translate("Activity") }}</p>
								<p class="text-sm text-gray-700">
									{{ log.activity_type || "-" }}
								</p>
							</div>
							<div>
								<p class="text-xs text-gray-500 md:hidden">{{ translate("Time") }}</p>
								<p class="text-sm text-gray-700">{{ formatRange(log) }}</p>
							</div>
							<div>
								<p class="text-xs text-gray-500 md:hidden">
									{{ translate("Description") }}
								</p>
								<p class="text-sm text-gray-600 whitespace-pre-wrap break-words">
									{{ log.description || translate("No description") }}
								</p>
							</div>
							<div>
								<p class="text-xs text-gray-500 md:hidden">{{ translate("Hours") }}</p>
								<p class="text-sm font-semibold text-gray-900">
									{{ formatHours(log.hours) }}
								</p>
							</div>
							<div class="flex items-center justify-between md:justify-end gap-2">
								<span
									class="px-2 py-0.5 rounded-full text-xs font-medium"
									:class="getStatusClass(log.status)"
								>
									{{ translate(log.status || "Unknown") }}
								</span>
								<button
									v-if="isDraftLog(log)"
									type="button"
									@click="openEditModal(log)"
									class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
									:title="translate('Edit draft entry')"
								>
									<Pencil class="w-4 h-4" />
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<Transition name="fade">
			<div
				v-if="editModalOpen"
				class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
			>
				<div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl">
					<div class="flex items-center justify-between px-5 py-4 border-b border-gray-200">
						<h2 class="text-lg font-semibold text-gray-900">
							{{ translate("Edit draft time entry") }}
						</h2>
						<button
							type="button"
							@click="closeEditModal"
							class="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100"
						>
							<X class="w-4 h-4" />
						</button>
					</div>
					<div class="p-5 space-y-4">
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("Hours") }}
								</label>
								<input
									v-model="editForm.hours"
									type="number"
									min="0"
									step="0.25"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								/>
							</div>
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("Activity type") }}
								</label>
								<select
									v-model="editForm.activity_type"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								>
									<option value="">{{ translate("Select activity") }}</option>
									<option
										v-for="activity in activityTypeOptions"
										:key="activity"
										:value="activity"
									>
										{{ activity }}
									</option>
								</select>
							</div>
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("From") }}
								</label>
								<input
									v-model="editForm.from_time"
									type="datetime-local"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								/>
							</div>
							<div>
								<label class="text-xs font-medium text-gray-500">
									{{ translate("To") }}
								</label>
								<input
									v-model="editForm.to_time"
									type="datetime-local"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								/>
							</div>
						</div>
						<div>
							<label class="text-xs font-medium text-gray-500">
								{{ translate("Description") }}
							</label>
							<textarea
								v-model="editForm.description"
								rows="3"
								class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
							></textarea>
						</div>
					</div>
					<div class="px-5 py-4 border-t border-gray-200 flex items-center justify-end gap-2">
						<button
							type="button"
							@click="closeEditModal"
							class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
						>
							{{ translate("Cancel") }}
						</button>
						<button
							type="button"
							@click="handleEditSave"
							:disabled="savingEdit"
							class="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors disabled:opacity-60"
						>
							{{ savingEdit ? translate("Saving...") : translate("Save changes") }}
						</button>
					</div>
				</div>
			</div>
		</Transition>
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
