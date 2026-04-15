<script setup>
import { ref, computed, onMounted, watch } from "vue";
import {
	ClipboardList,
	Search,
	Filter,
	X,
	RefreshCw,
	Trash2,
	ArrowUpDown,
	Users,
	AlertCircle,
	CheckCircle,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import BackToDeskButton from "../components/BackToDeskButton.vue";
import { useManagerTimeLogsStore } from "../stores/managerTimeLogsStore";
import { useTaskStore } from "../stores/taskStore";
import { getRealWindow, translate } from "../utils/translation";
import { useDebounceFn } from "../utils/composables";

const store = useManagerTimeLogsStore();
const taskStore = useTaskStore();
const realWindow = getRealWindow();

const showFilters = ref(false);
const searchInput = ref("");

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
	() =>
		new Intl.NumberFormat(userLocale.value, {
			minimumFractionDigits: 0,
			maximumFractionDigits: 2,
		})
);

const statusOptions = ["Draft", "Submitted", "Billed"];

const projectOptions = computed(() => {
	const map = new Map();
	store.projectChoices.forEach((project) => {
		map.set(project.name, {
			value: project.name,
			label: project.project_name || project.name,
		});
	});
	store.timelogs.forEach((log) => {
		if (log.project && !map.has(log.project)) {
			map.set(log.project, {
				value: log.project,
				label: log.project_name || log.project,
			});
		}
	});
	return Array.from(map.values());
});

const activityTypeOptions = computed(() => {
	if (taskStore.activityTypes.length > 0) {
		return taskStore.activityTypes;
	}
	const set = new Set();
	store.timelogs.forEach((log) => {
		if (log.activity_type) set.add(log.activity_type);
	});
	return Array.from(set.values());
});

const totalHours = computed(() =>
	store.timelogs.reduce((sum, log) => sum + (parseFloat(log.hours) || 0), 0)
);

const submittedHours = computed(() =>
	store.timelogs
		.filter((log) => log.status === "Submitted" || log.docstatus === 1)
		.reduce((sum, log) => sum + (parseFloat(log.hours) || 0), 0)
);

const draftHours = computed(() =>
	store.timelogs
		.filter((log) => log.status === "Draft" || log.docstatus === 0)
		.reduce((sum, log) => sum + (parseFloat(log.hours) || 0), 0)
);

const sortBy = ref("date");
const sortOrder = ref("desc");

const sortedTimelogs = computed(() => {
	const logs = [...store.timelogs];
	logs.sort((a, b) => {
		let compareValue = 0;
		switch (sortBy.value) {
			case "date":
				compareValue =
					new Date(a.from_time || a.creation) - new Date(b.from_time || b.creation);
				break;
			case "employee":
				compareValue = (a.owner_full_name || a.owner || "").localeCompare(
					b.owner_full_name || b.owner || ""
				);
				break;
			case "status":
				compareValue = (a.status || "").localeCompare(b.status || "");
				break;
			case "project":
				compareValue = (a.project_name || a.project || "").localeCompare(
					b.project_name || b.project || ""
				);
				break;
			case "hours":
				compareValue = (parseFloat(a.hours) || 0) - (parseFloat(b.hours) || 0);
				break;
			default:
				compareValue = 0;
		}
		return sortOrder.value === "asc" ? compareValue : -compareValue;
	});
	return logs;
});

const activeFilterChips = computed(() => {
	const chips = [];
	if (store.filters.search) {
		chips.push({ key: "search", label: `${translate("Search")}: ${store.filters.search}` });
	}
	if (store.filters.employee) {
		const emp = store.employeeChoices.find((e) => e.user === store.filters.employee);
		chips.push({
			key: "employee",
			label: `${translate("Employee")}: ${emp?.full_name || store.filters.employee}`,
		});
	}
	if (store.filters.status) {
		chips.push({
			key: "status",
			label: `${translate("Status")}: ${translate(store.filters.status)}`,
		});
	}
	if (store.filters.project) {
		const projectOption = projectOptions.value.find((p) => p.value === store.filters.project);
		chips.push({
			key: "project",
			label: `${translate("Project")}: ${projectOption?.label || store.filters.project}`,
		});
	}
	if (store.filters.activityType) {
		chips.push({
			key: "activityType",
			label: `${translate("Activity")}: ${store.filters.activityType}`,
		});
	}
	if (store.filters.startDate) {
		chips.push({
			key: "startDate",
			label: `${translate("Start date")}: ${formatChipDate(store.filters.startDate)}`,
		});
	}
	if (store.filters.endDate) {
		chips.push({
			key: "endDate",
			label: `${translate("End date")}: ${formatChipDate(store.filters.endDate)}`,
		});
	}
	return chips;
});

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
	applyMonthPreset(0, false);
	await Promise.all([
		store.fetchProjectChoices(),
		store.fetchEmployeeChoices(),
	]);
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

function removeFilter(key) {
	if (key === "search") searchInput.value = "";
	store.setFilter(key, "");
	store.fetchLogs();
}

function formatChipDate(value) {
	if (!value) return "";
	const [year, month, day] = value.split("-");
	if (!year || !month || !day) return value;
	return `${day}.${month}.${year}`;
}

function applyMonthPreset(monthsAgo, shouldFetch = true) {
	const today = new Date();
	const year = today.getFullYear();
	const month = today.getMonth() - monthsAgo;
	const start = new Date(year, month, 1);
	const end = new Date(year, month + 1, 0);
	const formatDate = (date) => {
		const pad = (n) => String(n).padStart(2, "0");
		return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
	};
	store.setFilter("startDate", formatDate(start));
	store.setFilter("endDate", formatDate(end));
	if (shouldFetch) store.fetchLogs();
}

function toggleSort(field) {
	if (sortBy.value === field) {
		sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
	} else {
		sortBy.value = field;
		sortOrder.value = "desc";
	}
}

function formatDateTime(value) {
	if (!value) return "";
	const normalized = value.replace(" ", "T");
	const date = new Date(normalized);
	if (Number.isNaN(date.getTime())) return value;
	return dateFormatter.value.format(date);
}

function formatHours(value) {
	const hours = parseFloat(value);
	if (Number.isNaN(hours)) return "0";
	return hoursFormatter.value.format(hours);
}

function isDraftLog(log) {
	return log?.status === "Draft" || log?.docstatus === 0;
}

function getStatusBadgeClass(status) {
	if (status === "Submitted") return "bg-emerald-100 text-emerald-800";
	if (status === "Draft") return "bg-amber-100 text-amber-800";
	if (status === "Billed") return "bg-blue-100 text-blue-800";
	return "bg-gray-100 text-gray-700";
}

function showAlert(message, indicator = "blue") {
	if (realWindow?.frappe) {
		realWindow.frappe.show_alert({ message, indicator });
	}
}

const expandedDescriptions = ref(new Set());

function toggleDescription(logName) {
	if (expandedDescriptions.value.has(logName)) {
		expandedDescriptions.value.delete(logName);
	} else {
		expandedDescriptions.value.add(logName);
	}
}

function getDescriptionText(log) {
	if (!log.description) return translate("No description");
	const limit = 80;
	if (log.description.length <= limit) return log.description;
	return expandedDescriptions.value.has(log.timelog_name)
		? log.description
		: `${log.description.slice(0, limit)}…`;
}

async function handleDeleteLog(log) {
	if (!isDraftLog(log)) {
		showAlert(translate("Only draft time entries can be deleted"), "orange");
		return;
	}
	if (!confirm(translate("Are you sure you want to delete this draft time entry?"))) return;
	try {
		await store.deleteTimelog(log.timelog_name);
		showAlert(translate("Time entry deleted"), "green");
	} catch (error) {
		showAlert(translate("Failed to delete time entry"), "red");
	}
}
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="w-full px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<ClipboardList class="w-6 h-6 text-emerald-600" />
						<h1 class="text-xl font-semibold text-gray-900">
							{{ translate("All Time Logs") }}
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
					</div>
				</div>
			</div>
		</header>

		<!-- Toolbar -->
		<div class="bg-white border-b border-gray-200 sticky top-16 z-10">
			<div class="w-full px-4 sm:px-6 lg:px-8 py-3">
				<!-- Summary Cards -->
				<div class="grid grid-cols-3 gap-3 mb-3">
					<div class="bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200 rounded-xl p-3 shadow-sm">
						<p class="text-xs font-medium text-emerald-700 uppercase tracking-wide">
							{{ translate("Total hours") }}
						</p>
						<p class="mt-1 text-2xl font-bold text-emerald-900">
							{{ formatHours(totalHours) }}h
						</p>
						<p class="text-xs text-emerald-600 mt-1">
							{{ store.total }} {{ translate("entries") }}
						</p>
					</div>
					<div class="bg-gradient-to-br from-amber-50 to-amber-100 border border-amber-200 rounded-xl p-3 shadow-sm">
						<p class="text-xs font-medium text-amber-700 uppercase tracking-wide">
							{{ translate("Draft") }}
						</p>
						<p class="mt-1 text-2xl font-bold text-amber-900">
							{{ formatHours(draftHours) }}h
						</p>
					</div>
					<div class="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl p-3 shadow-sm">
						<p class="text-xs font-medium text-blue-700 uppercase tracking-wide">
							{{ translate("Submitted") }}
						</p>
						<p class="mt-1 text-2xl font-bold text-blue-900">
							{{ formatHours(submittedHours) }}h
						</p>
					</div>
				</div>

				<!-- Search + filter bar -->
				<div class="flex items-center gap-2">
					<div class="relative flex-1">
						<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
						<input
							v-model="searchInput"
							type="text"
							:placeholder="translate('Search time logs...')"
							class="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white"
						/>
					</div>

					<button
						@click="showFilters = !showFilters"
						:class="[
							'flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors',
							showFilters || store.hasActiveFilters
								? 'bg-emerald-50 border-emerald-300 text-emerald-700'
								: 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50',
						]"
					>
						<Filter class="w-4 h-4" />
						<span>{{ translate("Filters") }}</span>
						<span
							v-if="activeFilterChips.length > 0"
							class="bg-emerald-600 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center"
						>
							{{ activeFilterChips.length }}
						</span>
					</button>

					<button
						@click="store.fetchLogs()"
						:disabled="store.loading"
						class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
						:title="translate('Refresh')"
					>
						<RefreshCw class="w-4 h-4" :class="{ 'animate-spin': store.loading }" />
					</button>
				</div>

				<!-- Active filter chips -->
				<div v-if="activeFilterChips.length > 0" class="flex flex-wrap gap-1.5 mt-2">
					<span
						v-for="chip in activeFilterChips"
						:key="chip.key"
						class="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-100 text-emerald-800 text-xs rounded-full"
					>
						{{ chip.label }}
						<button @click="removeFilter(chip.key)" class="hover:text-emerald-900">
							<X class="w-3 h-3" />
						</button>
					</span>
					<button
						@click="resetFilters"
						class="text-xs text-gray-500 hover:text-gray-700 underline"
					>
						{{ translate("Clear all") }}
					</button>
				</div>

				<!-- Filter panel -->
				<div v-if="showFilters" class="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
					<!-- Employee filter -->
					<div>
						<label class="block text-xs font-medium text-gray-600 mb-1">
							<Users class="w-3 h-3 inline mr-1" />{{ translate("Employee") }}
						</label>
						<select
							:value="store.filters.employee"
							@change="updateFilter('employee', $event.target.value)"
							class="w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
						>
							<option value="">{{ translate("All employees") }}</option>
							<option v-for="emp in store.employeeChoices" :key="emp.user" :value="emp.user">
								{{ emp.full_name || emp.user }}
							</option>
						</select>
					</div>

					<!-- Status filter -->
					<div>
						<label class="block text-xs font-medium text-gray-600 mb-1">{{ translate("Status") }}</label>
						<select
							:value="store.filters.status"
							@change="updateFilter('status', $event.target.value)"
							class="w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
						>
							<option value="">{{ translate("All statuses") }}</option>
							<option v-for="s in statusOptions" :key="s" :value="s">{{ translate(s) }}</option>
						</select>
					</div>

					<!-- Project filter -->
					<div>
						<label class="block text-xs font-medium text-gray-600 mb-1">{{ translate("Project") }}</label>
						<select
							:value="store.filters.project"
							@change="updateFilter('project', $event.target.value)"
							class="w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
						>
							<option value="">{{ translate("All projects") }}</option>
							<option v-for="p in projectOptions" :key="p.value" :value="p.value">
								{{ p.label }}
							</option>
						</select>
					</div>

					<!-- Activity type filter -->
					<div>
						<label class="block text-xs font-medium text-gray-600 mb-1">{{ translate("Activity") }}</label>
						<select
							:value="store.filters.activityType"
							@change="updateFilter('activityType', $event.target.value)"
							class="w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
						>
							<option value="">{{ translate("All activities") }}</option>
							<option v-for="a in activityTypeOptions" :key="a" :value="a">{{ a }}</option>
						</select>
					</div>

					<!-- Date range -->
					<div>
						<label class="block text-xs font-medium text-gray-600 mb-1">{{ translate("Start date") }}</label>
						<input
							type="date"
							:value="store.filters.startDate"
							@change="updateFilter('startDate', $event.target.value)"
							class="w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
						/>
					</div>
					<div>
						<label class="block text-xs font-medium text-gray-600 mb-1">{{ translate("End date") }}</label>
						<input
							type="date"
							:value="store.filters.endDate"
							@change="updateFilter('endDate', $event.target.value)"
							class="w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
						/>
					</div>

					<!-- Quick presets -->
					<div class="col-span-2 sm:col-span-3 lg:col-span-4 flex gap-2 flex-wrap">
						<button
							@click="applyMonthPreset(0)"
							class="text-xs px-2 py-1 bg-white border border-gray-200 rounded hover:bg-emerald-50 hover:border-emerald-300 transition-colors"
						>
							{{ translate("This month") }}
						</button>
						<button
							@click="applyMonthPreset(1)"
							class="text-xs px-2 py-1 bg-white border border-gray-200 rounded hover:bg-emerald-50 hover:border-emerald-300 transition-colors"
						>
							{{ translate("Last month") }}
						</button>
						<button
							@click="resetFilters"
							class="text-xs px-2 py-1 bg-white border border-red-200 text-red-600 rounded hover:bg-red-50 transition-colors ml-auto"
						>
							{{ translate("Reset all") }}
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Content -->
		<main class="w-full px-4 sm:px-6 lg:px-8 py-6">
			<!-- Loading -->
			<div v-if="store.loading" class="flex items-center justify-center py-16">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
			</div>

			<!-- Error -->
			<div
				v-else-if="store.error"
				class="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700"
			>
				<AlertCircle class="w-5 h-5 flex-shrink-0" />
				<span>{{ store.error }}</span>
			</div>

			<!-- Empty state -->
			<div
				v-else-if="sortedTimelogs.length === 0"
				class="text-center py-16 bg-white rounded-lg border border-gray-200"
			>
				<ClipboardList class="w-12 h-12 text-gray-300 mx-auto mb-4" />
				<p class="text-gray-500">{{ translate("No time logs found") }}</p>
				<button
					v-if="store.hasActiveFilters"
					@click="resetFilters"
					class="mt-3 text-sm text-emerald-600 hover:underline"
				>
					{{ translate("Clear filters") }}
				</button>
			</div>

			<!-- Table -->
			<div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
				<!-- Desktop table -->
				<div class="hidden sm:block overflow-x-auto">
					<table class="w-full text-sm">
						<thead class="bg-gray-50 border-b border-gray-200">
							<tr>
								<th
									class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
									@click="toggleSort('date')"
								>
									<div class="flex items-center gap-1">
										{{ translate("Date") }}
										<ArrowUpDown class="w-3 h-3" />
									</div>
								</th>
								<th
									class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
									@click="toggleSort('employee')"
								>
									<div class="flex items-center gap-1">
										{{ translate("Employee") }}
										<ArrowUpDown class="w-3 h-3" />
									</div>
								</th>
								<th
									class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
									@click="toggleSort('project')"
								>
									<div class="flex items-center gap-1">
										{{ translate("Project") }}
										<ArrowUpDown class="w-3 h-3" />
									</div>
								</th>
								<th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
									{{ translate("Activity / Description") }}
								</th>
								<th
									class="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
									@click="toggleSort('hours')"
								>
									<div class="flex items-center justify-end gap-1">
										{{ translate("Hours") }}
										<ArrowUpDown class="w-3 h-3" />
									</div>
								</th>
								<th
									class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
									@click="toggleSort('status')"
								>
									<div class="flex items-center gap-1">
										{{ translate("Status") }}
										<ArrowUpDown class="w-3 h-3" />
									</div>
								</th>
								<th class="px-4 py-3 w-10"></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<tr
								v-for="log in sortedTimelogs"
								:key="log.timelog_name"
								class="hover:bg-gray-50 transition-colors"
							>
								<!-- Date -->
								<td class="px-4 py-3 text-gray-600 whitespace-nowrap text-xs">
									{{ formatDateTime(log.from_time) }}
								</td>

								<!-- Employee -->
								<td class="px-4 py-3">
									<div class="flex items-center gap-2">
										<div class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-semibold flex-shrink-0">
											{{ (log.owner_full_name || log.owner || "?").charAt(0).toUpperCase() }}
										</div>
										<span class="text-sm text-gray-800 font-medium truncate max-w-[120px]">
											{{ log.owner_full_name || log.owner }}
										</span>
									</div>
								</td>

								<!-- Project -->
								<td class="px-4 py-3">
									<span
										v-if="log.project"
										class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-blue-50 text-blue-700 max-w-[140px] truncate"
									>
										{{ log.project_name || log.project }}
									</span>
									<span v-else class="text-gray-400 text-xs">—</span>
								</td>

								<!-- Activity / Description -->
								<td class="px-4 py-3 max-w-xs">
									<div class="text-xs font-medium text-gray-700 mb-0.5">
										{{ log.activity_type || "—" }}
									</div>
									<div class="text-xs text-gray-500">
										{{ getDescriptionText(log) }}
										<button
											v-if="log.description && log.description.length > 80"
											@click="toggleDescription(log.timelog_name)"
											class="text-emerald-600 hover:underline ml-1"
										>
											{{
												expandedDescriptions.has(log.timelog_name)
													? translate("less")
													: translate("more")
											}}
										</button>
									</div>
									<div v-if="log.task_subject" class="text-xs text-gray-400 mt-0.5 truncate">
										{{ log.task_subject }}
									</div>
								</td>

								<!-- Hours -->
								<td class="px-4 py-3 text-right font-semibold text-gray-900 whitespace-nowrap">
									{{ formatHours(log.hours) }}h
								</td>

								<!-- Status -->
								<td class="px-4 py-3">
									<span
										:class="[
											'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
											getStatusBadgeClass(log.status),
										]"
									>
										<CheckCircle v-if="log.status === 'Submitted'" class="w-3 h-3" />
										{{ translate(log.status) }}
									</span>
								</td>

								<!-- Actions -->
								<td class="px-4 py-3">
									<button
										v-if="isDraftLog(log)"
										@click="handleDeleteLog(log)"
										class="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
										:title="translate('Delete')"
									>
										<Trash2 class="w-4 h-4" />
									</button>
								</td>
							</tr>
						</tbody>
					</table>
				</div>

				<!-- Mobile cards -->
				<div class="sm:hidden divide-y divide-gray-100">
					<div
						v-for="log in sortedTimelogs"
						:key="log.timelog_name"
						class="p-4 hover:bg-gray-50"
					>
						<div class="flex items-start justify-between mb-2">
							<div class="flex items-center gap-2">
								<div class="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-semibold">
									{{ (log.owner_full_name || log.owner || "?").charAt(0).toUpperCase() }}
								</div>
								<div>
									<div class="text-sm font-medium text-gray-900">
										{{ log.owner_full_name || log.owner }}
									</div>
									<div class="text-xs text-gray-500">
										{{ formatDateTime(log.from_time) }}
									</div>
								</div>
							</div>
							<div class="flex items-center gap-2">
								<span class="font-semibold text-gray-900">{{ formatHours(log.hours) }}h</span>
								<span
									:class="[
										'px-2 py-0.5 rounded-full text-xs font-medium',
										getStatusBadgeClass(log.status),
									]"
								>
									{{ translate(log.status) }}
								</span>
							</div>
						</div>
						<div v-if="log.project" class="mb-1">
							<span class="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
								{{ log.project_name || log.project }}
							</span>
						</div>
						<div class="text-xs text-gray-600">
							<span class="font-medium">{{ log.activity_type }}</span>
							<span v-if="log.description" class="text-gray-500"> — {{ getDescriptionText(log) }}</span>
						</div>
						<div v-if="isDraftLog(log)" class="mt-2 flex justify-end">
							<button
								@click="handleDeleteLog(log)"
								class="text-xs text-red-500 hover:text-red-700 flex items-center gap-1"
							>
								<Trash2 class="w-3 h-3" />{{ translate("Delete") }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</main>

		<BackToDeskButton />
	</div>
</template>
