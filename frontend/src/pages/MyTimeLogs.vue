<script setup>
import { ref, computed, onMounted, watch } from "vue";
import {
	Timer,
	Search,
	Filter,
	X,
	RefreshCw,
	Pencil,
	AlertCircle,
	Trash2,
	ArrowUpDown,
	Calendar as CalendarIcon,
	List,
	CalendarDays,
	ChevronLeft,
	ChevronRight,
	CheckCircle,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import BackToDeskButton from "../components/BackToDeskButton.vue";
import { useMyTimeLogsStore } from "../stores/myTimeLogsStore";
import { useTaskStore } from "../stores/taskStore";
import { getRealWindow, translate } from "../utils/translation";
import { useDebounceFn } from "../utils/composables";

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
	project: "",
	is_billable: false,
});

// Helper function for week calculations
function getWeekStart(date) {
	const d = new Date(date);
	const day = d.getDay();
	const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
	return new Date(d.setDate(diff));
}

// Helper function to get local date string in YYYY-MM-DD format
function getLocalDateString(date) {
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, "0");
	const day = String(date.getDate()).padStart(2, "0");
	return `${year}-${month}-${day}`;
}

// View mode and sorting
const viewMode = ref("list"); // 'list' | 'calendar' | 'week'
const sortBy = ref("date");
const sortOrder = ref("desc");

// Calendar navigation
const currentCalendarDate = ref(new Date());

// Week view navigation
const currentWeekStart = ref(getWeekStart(new Date()));

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

const submittedHours = computed(() =>
	store.timelogs
		.filter((log) => log.status === "Submitted" || log.docstatus === 1)
		.reduce((sum, log) => sum + (parseFloat(log.hours) || 0), 0)
);

const draftPercentage = computed(() => {
	if (totalHours.value === 0) return 0;
	return (draftHours.value / totalHours.value) * 100;
});

const submittedPercentage = computed(() => {
	if (totalHours.value === 0) return 0;
	return (submittedHours.value / totalHours.value) * 100;
});

// Sorted and filtered timelogs
const sortedTimelogs = computed(() => {
	const logs = [...store.timelogs];

	logs.sort((a, b) => {
		let compareValue = 0;

		switch (sortBy.value) {
			case "date":
				compareValue = new Date(a.from_time || a.creation) - new Date(b.from_time || b.creation);
				break;
			case "status":
				compareValue = (a.status || "").localeCompare(b.status || "");
				break;
			case "project":
				compareValue = (a.project_name || a.project || "").localeCompare(b.project_name || b.project || "");
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

// Calendar view data - group logs by date
const calendarData = computed(() => {
	const data = {};

	sortedTimelogs.value.forEach((log) => {
		const date = log.from_time ? log.from_time.split(" ")[0] : log.creation?.split(" ")[0];
		if (!date) return;

		if (!data[date]) {
			data[date] = {
				logs: [],
				totalHours: 0,
				draftHours: 0,
				submittedHours: 0,
			};
		}

		data[date].logs.push(log);
		const hours = parseFloat(log.hours) || 0;
		data[date].totalHours += hours;

		if (isDraftLog(log)) {
			data[date].draftHours += hours;
		} else if (log.status === "Submitted") {
			data[date].submittedHours += hours;
		}
	});

	return data;
});

// Week view data - get days for current week
const weekDays = computed(() => {
	const days = [];
	const start = new Date(currentWeekStart.value);

	for (let i = 0; i < 7; i++) {
		const date = new Date(start);
		date.setDate(start.getDate() + i);
		const dateStr = getLocalDateString(date);

		days.push({
			date: date,
			dateStr: dateStr,
			data: calendarData.value[dateStr] || {
				logs: [],
				totalHours: 0,
				draftHours: 0,
				submittedHours: 0,
			},
		});
	}

	return days;
});

// Calendar month data
const calendarMonth = computed(() => {
	const year = currentCalendarDate.value.getFullYear();
	const month = currentCalendarDate.value.getMonth();

	const firstDay = new Date(year, month, 1);
	const startDate = new Date(firstDay);
	const dayOfWeek = firstDay.getDay();
	// Adjust for Monday-first week: Sunday goes back 6 days, Mon goes back 0
	const daysToSubtract = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
	startDate.setDate(startDate.getDate() - daysToSubtract);

	const weeks = [];
	let currentWeek = [];
	const currentDate = new Date(startDate);
	const totalCells = 6 * 7; // 6 weeks to cover all possible layouts

	for (let cell = 0; cell < totalCells; cell++) {
		const dateStr = getLocalDateString(currentDate);
		const isCurrentMonth = currentDate.getMonth() === month;

		currentWeek.push({
			date: new Date(currentDate),
			dateStr,
			isCurrentMonth,
			data: calendarData.value[dateStr] || {
				logs: [],
				totalHours: 0,
				draftHours: 0,
				submittedHours: 0,
			},
		});

		if (currentWeek.length === 7) {
			weeks.push(currentWeek);
			currentWeek = [];
		}

		currentDate.setDate(currentDate.getDate() + 1);
	}

	// Remove trailing weeks with no days from current month
	while (
		weeks.length > 0 &&
		weeks[weeks.length - 1].every((day) => !day.isCurrentMonth)
	) {
		weeks.pop();
	}

	return weeks;
});

const activeFilterChips = computed(() => {
	const chips = [];
	if (store.filters.search) {
		chips.push({
			key: "search",
			label: `${translate("Search")}: ${store.filters.search}`,
		});
	}
	if (store.filters.status) {
		chips.push({
			key: "status",
			label: `${translate("Status")}: ${translate(store.filters.status)}`,
		});
	}
	if (store.filters.project) {
		const projectOption = projectOptions.value.find((item) => item.value === store.filters.project);
		chips.push({
			key: "project",
			label: `${translate("Project")}: ${
				projectOption?.label || store.filters.project
			}`,
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
	await store.fetchProjectChoices();
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
	if (key === "search") {
		searchInput.value = "";
	}
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
	if (shouldFetch) {
		store.fetchLogs();
	}
}

function toggleSort(field) {
	if (sortBy.value === field) {
		sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
	} else {
		sortBy.value = field;
		sortOrder.value = "desc";
	}
}

function navigateCalendar(direction) {
	const newDate = new Date(currentCalendarDate.value);
	newDate.setMonth(newDate.getMonth() + direction);
	currentCalendarDate.value = newDate;
}

function navigateWeek(direction) {
	const newDate = new Date(currentWeekStart.value);
	newDate.setDate(newDate.getDate() + direction * 7);
	currentWeekStart.value = newDate;
}

function goToToday() {
	if (viewMode.value === "calendar") {
		currentCalendarDate.value = new Date();
	} else if (viewMode.value === "week") {
		currentWeekStart.value = getWeekStart(new Date());
	}
}

function formatMonthYear(date) {
	return new Intl.DateTimeFormat(userLocale.value, {
		year: "numeric",
		month: "long",
	}).format(date);
}

function formatDayName(date) {
	return new Intl.DateTimeFormat(userLocale.value, { weekday: "short" }).format(date);
}

function formatDayMonth(date) {
	return new Intl.DateTimeFormat(userLocale.value, {
		month: "short",
		day: "numeric",
	}).format(date);
}

function isToday(date) {
	const today = new Date();
	return (
		date.getDate() === today.getDate() &&
		date.getMonth() === today.getMonth() &&
		date.getFullYear() === today.getFullYear()
	);
}

function toggleDraftsOnly() {
	const next = store.filters.status === "Draft" ? "" : "Draft";
	updateFilter("status", next);
}

function isDraftLog(log) {
	return log?.status === "Draft" || log?.docstatus === 0;
}

function formatDateTime(value) {
	if (!value) return "";
	const normalized = value.replace(" ", "T");
	const date = new Date(normalized);
	if (Number.isNaN(date.getTime())) return value;
	return dateFormatter.value.format(date);
}

function formatStartTime(log) {
	if (!log?.from_time) return "";
	return formatDateTime(log.from_time);
}

function formatHours(value) {
	const hours = parseFloat(value);
	if (Number.isNaN(hours)) return "0";
	return hoursFormatter.value.format(hours);
}

const expandedDescriptions = ref(new Set());

function toggleDescription(logName) {
	if (expandedDescriptions.value.has(logName)) {
		expandedDescriptions.value.delete(logName);
	} else {
		expandedDescriptions.value.add(logName);
	}
}

function isDescriptionExpanded(logName) {
	return expandedDescriptions.value.has(logName);
}

function getDescriptionText(log) {
	if (!log.description) return translate("No description");
	const limit = 100;
	if (log.description.length <= limit) {
		return log.description;
	}
	return isDescriptionExpanded(log.timelog_name)
		? log.description
		: `${log.description.slice(0, limit)}…`;
}

function shouldShowMoreButton(log) {
	return log.description && log.description.length > 100;
}

function getProjectInitial(log) {
	const label = log.project_name || log.project || "";
	return label.trim() ? label.trim().charAt(0).toUpperCase() : "P";
}

function getStatusBadgeClass(status) {
	if (status === "Submitted") return "bg-emerald-100 text-emerald-800";
	if (status === "Draft") return "bg-amber-100 text-amber-800";
	if (status === "Billed") return "bg-blue-100 text-blue-800";
	return "bg-gray-100 text-gray-700";
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
		project: log.project || "",
		is_billable: Boolean(log.is_billable),
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
		project: "",
		is_billable: false,
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
			is_billable: editForm.value.is_billable ? 1 : 0,
		};
		if (editForm.value.from_time) {
			payload.from_time = toFrappeDateTime(editForm.value.from_time);
		}
		if (editForm.value.to_time) {
			payload.to_time = toFrappeDateTime(editForm.value.to_time);
		}
		if (editForm.value.project) {
			payload.project = editForm.value.project;
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

async function handleDeleteLog(log) {
	if (!isDraftLog(log)) return;
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
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="w-full px-4 sm:px-6 lg:px-8">
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
					</div>
				</div>
			</div>
		</header>

		<div class="bg-white border-b border-gray-200 sticky top-16 z-10">
			<div class="w-full px-4 sm:px-6 lg:px-8 py-3">
				<!-- Summary Cards Row -->
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
					<!-- Total Hours Card -->
					<div class="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl p-3 shadow-sm">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-xs font-medium text-blue-700 uppercase tracking-wide">
									{{ translate("Total hours") }}
								</p>
								<p class="mt-1 text-3xl font-bold text-blue-900">
									{{ formatHours(totalHours) }}
								</p>
								<p class="text-xs text-blue-600 mt-0.5">
									{{ store.timelogs.length }} {{ translate("entries") }}
								</p>
							</div>
							<Timer class="w-10 h-10 text-blue-600 opacity-60" />
						</div>
					</div>

					<!-- Draft Hours Card -->
					<div class="bg-gradient-to-br from-amber-50 to-amber-100 border border-amber-200 rounded-xl p-3 shadow-sm">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-xs font-medium text-amber-700 uppercase tracking-wide">
									{{ translate("Draft hours") }}
								</p>
								<p class="mt-1 text-3xl font-bold text-amber-900">
									{{ formatHours(draftHours) }}
								</p>
								<p class="text-xs text-amber-600 mt-0.5">
									{{ draftCount }} {{ translate("drafts") }}
								</p>
							</div>
							<Pencil class="w-10 h-10 text-amber-600 opacity-60" />
						</div>
					</div>

					<!-- Submitted Hours Card -->
					<div class="bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200 rounded-xl p-3 shadow-sm">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-xs font-medium text-emerald-700 uppercase tracking-wide">
									{{ translate("Submitted hours") }}
								</p>
								<p class="mt-1 text-3xl font-bold text-emerald-900">
									{{ formatHours(submittedHours) }}
								</p>
								<p class="text-xs text-emerald-600 mt-0.5">
									{{ (store.timelogs.length - draftCount) }} {{ translate("submitted") }}
								</p>
							</div>
							<CheckCircle class="w-10 h-10 text-emerald-600 opacity-60" />
						</div>
					</div>
				</div>

				<!-- Progress Bar -->
				<div v-if="totalHours > 0" class="mb-4">
					<div class="flex items-center justify-between text-xs text-gray-600 mb-1.5">
						<span>{{ translate("Progress") }}</span>
						<span>{{ formatHours(submittedHours) }} / {{ formatHours(totalHours) }} {{ translate("hrs submitted") }}</span>
					</div>
					<div class="h-3 bg-gray-200 rounded-full overflow-hidden flex">
						<div
							class="bg-gradient-to-r from-emerald-500 to-emerald-600 transition-all duration-500"
							:style="{ width: `${submittedPercentage}%` }"
							:title="`${translate('Submitted')}: ${formatHours(submittedHours)} hrs (${submittedPercentage.toFixed(1)}%)`"
						></div>
						<div
							class="bg-gradient-to-r from-amber-400 to-amber-500 transition-all duration-500"
							:style="{ width: `${draftPercentage}%` }"
							:title="`${translate('Draft')}: ${formatHours(draftHours)} hrs (${draftPercentage.toFixed(1)}%)`"
						></div>
					</div>
					<div class="flex items-center justify-between text-xs mt-1.5">
						<span class="flex items-center gap-1 text-emerald-700">
							<span class="w-3 h-3 rounded-full bg-emerald-500"></span>
							{{ submittedPercentage.toFixed(1) }}% {{ translate("Submitted") }}
						</span>
						<span class="flex items-center gap-1 text-amber-700">
							<span class="w-3 h-3 rounded-full bg-amber-500"></span>
							{{ draftPercentage.toFixed(1) }}% {{ translate("Draft") }}
						</span>
					</div>
				</div>

				<!-- Search and Filters Row -->
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

					<div class="flex items-center gap-2 flex-wrap">
						<!-- View Mode Toggle -->
						<div class="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
							<button
								@click="viewMode = 'list'"
								:class="[
									'p-2 rounded-md transition-colors',
									viewMode === 'list'
										? 'bg-white text-amber-600 shadow-sm'
										: 'text-gray-600 hover:text-gray-900',
								]"
								:title="translate('List view')"
							>
								<List class="w-4 h-4" />
							</button>
							<button
								@click="viewMode = 'calendar'"
								:class="[
									'p-2 rounded-md transition-colors',
									viewMode === 'calendar'
										? 'bg-white text-amber-600 shadow-sm'
										: 'text-gray-600 hover:text-gray-900',
								]"
								:title="translate('Calendar view')"
							>
								<CalendarIcon class="w-4 h-4" />
							</button>
							<button
								@click="viewMode = 'week'"
								:class="[
									'p-2 rounded-md transition-colors',
									viewMode === 'week'
										? 'bg-white text-amber-600 shadow-sm'
										: 'text-gray-600 hover:text-gray-900',
								]"
								:title="translate('Week view')"
							>
								<CalendarDays class="w-4 h-4" />
							</button>
						</div>

						<!-- Sort Dropdown (only in list view) -->
						<div v-if="viewMode === 'list'" class="relative">
							<select
								v-model="sortBy"
								@change="sortOrder = 'desc'"
								class="pl-3 pr-8 py-2 text-sm border border-gray-300 rounded-lg bg-white hover:bg-gray-50 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 appearance-none"
							>
								<option value="date">{{ translate("Sort by Date") }}</option>
								<option value="status">{{ translate("Sort by Status") }}</option>
								<option value="project">{{ translate("Sort by Project") }}</option>
								<option value="hours">{{ translate("Sort by Hours") }}</option>
							</select>
							<button
								@click="toggleSort(sortBy)"
								class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
							>
								<ArrowUpDown class="w-4 h-4" />
							</button>
						</div>

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
									placeholder="dd.mm.rrrr (08.01.2026)"
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
									placeholder="dd.mm.rrrr (08.01.2026)"
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
						<div class="mt-4 flex flex-wrap gap-2">
							<button
								type="button"
								@click="applyMonthPreset(0)"
								class="px-3 py-2 text-sm font-semibold text-amber-600 border border-amber-200 rounded-lg hover:bg-amber-50"
							>
								{{ translate("Current month") }}
							</button>
							<button
								type="button"
								@click="applyMonthPreset(1)"
								class="px-3 py-2 text-sm font-semibold text-amber-600 border border-amber-200 rounded-lg hover:bg-amber-50"
							>
								{{ translate("Previous month") }}
							</button>
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

		<div
			v-if="store.hasActiveFilters"
			class="w-full px-4 sm:px-6 lg:px-8 mt-3 flex flex-wrap items-center gap-2"
		>
			<div class="flex flex-wrap gap-2 items-center">
				<span
					v-for="chip in activeFilterChips"
					:key="chip.key"
					class="flex items-center gap-2 text-xs font-medium px-3 py-1 rounded-full border border-amber-200 bg-amber-50 text-amber-700"
				>
					{{ chip.label }}
					<button
						type="button"
						class="flex rounded-full hover:bg-amber-100"
						@click="removeFilter(chip.key)"
					>
						<X class="w-3 h-3" />
					</button>
				</span>
			</div>
			<button
				type="button"
				@click="resetFilters"
				class="ml-2 px-3 py-1 text-xs font-semibold text-gray-600 border border-gray-300 rounded-full hover:bg-gray-100"
			>
				{{ translate("Reset all filters") }}
			</button>
		</div>

		<div class="w-full px-4 sm:px-6 lg:px-8 py-6">
			<!-- LIST VIEW -->
			<div v-if="viewMode === 'list'" class="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
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

				<div v-else-if="sortedTimelogs.length === 0" class="py-12 text-center text-sm text-gray-500">
					{{ translate("No time entries found") }}
				</div>

				<div v-else class="space-y-4 p-4">
					<div v-for="log in sortedTimelogs" :key="log.timelog_name">
						<details
							class="group bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden"
							open
						>
							<summary class="flex cursor-pointer items-center justify-between gap-3 px-4 py-3">
								<div class="flex items-center gap-3">
									<div
										class="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100 text-sm font-semibold text-gray-700"
									>
										{{ getProjectInitial(log) }}
									</div>
									<div>
										<p class="text-sm font-semibold text-gray-900">
											{{ log.task_subject || log.task || translate("No task") }}
										</p>
										<p class="text-xs text-gray-500">
											{{ log.project_name || log.project || translate("No project") }}
										</p>
									</div>
								</div>
								<div class="flex flex-col items-end gap-1">
									<span
										class="px-3 py-1 text-xs font-semibold rounded-full"
										:class="getStatusBadgeClass(log.status)"
									>
										{{ translate(log.status || "Unknown") }}
									</span>
										<p class="text-xs text-gray-500">{{ formatStartTime(log) }}</p>
								</div>
							</summary>

							<div class="px-4 pb-4 space-y-3 border-t border-gray-100">
								<div class="grid grid-cols-2 gap-4">
									<div>
										<p class="text-xs text-gray-500">{{ translate("Activity") }}</p>
										<p class="text-sm text-gray-700">{{ log.activity_type || "-" }}</p>
									</div>
									<div>
										<p class="text-xs text-gray-500">{{ translate("Hours") }}</p>
										<p class="text-sm font-semibold text-gray-900">
											{{ formatHours(log.hours) }}
										</p>
									</div>
								</div>

								<div>
									<p class="text-xs text-gray-500">{{ translate("Description") }}</p>
									<p class="text-sm text-gray-600 whitespace-pre-wrap break-words">
										{{ getDescriptionText(log) }}
									</p>
									<button
										v-if="shouldShowMoreButton(log)"
										type="button"
										@click="toggleDescription(log.timelog_name)"
										class="mt-2 text-xs font-semibold text-amber-600 hover:text-amber-700"
									>
										{{ isDescriptionExpanded(log.timelog_name)
											? translate("Show less")
											: translate("Show more") }}
									</button>
								</div>

								<div class="flex flex-wrap gap-2">
									<button
										v-if="isDraftLog(log)"
										type="button"
										@click="openEditModal(log)"
										class="flex items-center gap-1 px-3 py-2 text-xs font-semibold text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
									>
										<Pencil class="w-4 h-4" />
										{{ translate("Edit") }}
									</button>
									<button
										v-if="isDraftLog(log)"
										type="button"
										@click="handleDeleteLog(log)"
										class="flex items-center gap-1 px-3 py-2 text-xs font-semibold text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
									>
										<Trash2 class="w-4 h-4" />
										{{ translate("Delete") }}
									</button>
								</div>
							</div>
						</details>
					</div>
				</div>
			</div>

			<!-- CALENDAR VIEW -->
			<div v-if="viewMode === 'calendar'" class="space-y-4">
				<!-- Calendar Navigation -->
				<div class="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
					<div class="flex items-center justify-between mb-4">
						<h2 class="text-lg font-semibold text-gray-900">
							{{ formatMonthYear(currentCalendarDate) }}
						</h2>
						<div class="flex items-center gap-2">
							<button
								@click="goToToday"
								class="px-3 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
							>
								{{ translate("Today") }}
							</button>
							<button
								@click="navigateCalendar(-1)"
								class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
							>
								<ChevronLeft class="w-5 h-5" />
							</button>
							<button
								@click="navigateCalendar(1)"
								class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
							>
								<ChevronRight class="w-5 h-5" />
							</button>
						</div>
					</div>

					<!-- Calendar Grid -->
					<div class="grid grid-cols-7 gap-2">
						<!-- Day headers -->
						<div
							v-for="day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']"
							:key="day"
							class="text-center text-xs font-semibold text-gray-500 uppercase py-2"
						>
							{{ translate(day) }}
						</div>

						<!-- Calendar days -->
						<div
							v-for="(day, index) in calendarMonth.flat()"
							:key="index"
							:class="[
								'min-h-24 p-2 rounded-lg border transition-colors',
								day.isCurrentMonth ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-100',
								isToday(day.date) && 'ring-2 ring-amber-500',
							]"
						>
							<div class="flex items-center justify-between mb-1">
								<span
									:class="[
										'text-sm font-medium',
										day.isCurrentMonth ? 'text-gray-900' : 'text-gray-400',
										isToday(day.date) && 'text-amber-600 font-bold',
									]"
								>
									{{ day.date.getDate() }}
								</span>
								<span
									v-if="day.data.totalHours > 0"
									class="text-xs font-semibold text-blue-600"
								>
									{{ formatHours(day.data.totalHours) }}h
								</span>
							</div>

							<!-- Hours breakdown -->
							<div v-if="day.data.totalHours > 0" class="space-y-1">
								<div
									v-if="day.data.submittedHours > 0"
									class="flex items-center justify-between text-xs"
								>
									<span class="text-emerald-600">{{ translate("Submitted") }}</span>
									<span class="font-medium text-emerald-700">
										{{ formatHours(day.data.submittedHours) }}h
									</span>
								</div>
								<div
									v-if="day.data.draftHours > 0"
									class="flex items-center justify-between text-xs"
								>
									<span class="text-amber-600">{{ translate("Draft") }}</span>
									<span class="font-medium text-amber-700">
										{{ formatHours(day.data.draftHours) }}h
									</span>
								</div>
								<div class="text-xs text-gray-500 mt-1">
									{{ day.data.logs.length }} {{ translate("entries") }}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- WEEK VIEW -->
			<div v-if="viewMode === 'week'" class="space-y-4">
				<!-- Week Navigation -->
				<div class="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
					<div class="flex items-center justify-between mb-4">
						<h2 class="text-lg font-semibold text-gray-900">
							{{ translate("Week View") }} -
							{{ formatDayMonth(weekDays[0].date) }} - {{ formatDayMonth(weekDays[6].date) }}
						</h2>
						<div class="flex items-center gap-2">
							<button
								@click="goToToday"
								class="px-3 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
							>
								{{ translate("This week") }}
							</button>
							<button
								@click="navigateWeek(-1)"
								class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
							>
								<ChevronLeft class="w-5 h-5" />
							</button>
							<button
								@click="navigateWeek(1)"
								class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
							>
								<ChevronRight class="w-5 h-5" />
							</button>
						</div>
					</div>

					<!-- Week Grid -->
					<div class="grid grid-cols-1 md:grid-cols-7 gap-3">
						<div
							v-for="day in weekDays"
							:key="day.dateStr"
							:class="[
								'bg-white border-2 rounded-xl p-3 transition-all',
								isToday(day.date)
									? 'border-amber-500 shadow-lg'
									: 'border-gray-200',
							]"
						>
							<!-- Day header -->
							<div class="mb-3">
								<div
									:class="[
										'text-xs font-medium uppercase',
										isToday(day.date) ? 'text-amber-600' : 'text-gray-500',
									]"
								>
									{{ formatDayName(day.date) }}
								</div>
								<div
									:class="[
										'text-lg font-bold',
										isToday(day.date) ? 'text-amber-600' : 'text-gray-900',
									]"
								>
									{{ day.date.getDate() }}
								</div>
							</div>

							<!-- Hours summary -->
							<div class="space-y-2 mb-3">
								<div class="flex items-center justify-between">
									<span class="text-xs font-medium text-gray-600">{{ translate("Total") }}</span>
									<span
										:class="[
											'text-sm font-bold',
											day.data.totalHours >= 8
												? 'text-emerald-600'
												: day.data.totalHours > 0
												? 'text-amber-600'
												: 'text-gray-400',
										]"
									>
										{{ formatHours(day.data.totalHours) }}h
									</span>
								</div>

								<!-- Goal progress bar (8 hours target) -->
								<div class="relative">
									<div class="h-2 bg-gray-100 rounded-full overflow-hidden">
										<div
											:class="[
												'h-full transition-all duration-500 rounded-full',
												day.data.totalHours >= 8
													? 'bg-emerald-500'
													: day.data.totalHours >= 4
													? 'bg-amber-500'
													: 'bg-blue-400',
											]"
											:style="{ width: `${Math.min((day.data.totalHours / 8) * 100, 100)}%` }"
										></div>
									</div>
									<div class="flex justify-between text-xs text-gray-500 mt-1">
										<span>0h</span>
										<span class="font-medium">8h</span>
									</div>
								</div>
							</div>

							<!-- Hours breakdown -->
							<div class="space-y-1.5">
								<div
									v-if="day.data.submittedHours > 0"
									class="flex items-center gap-2 text-xs"
								>
									<CheckCircle class="w-3 h-3 text-emerald-600" />
									<span class="text-emerald-700 font-medium">
										{{ formatHours(day.data.submittedHours) }}h {{ translate("submitted") }}
									</span>
								</div>
								<div
									v-if="day.data.draftHours > 0"
									class="flex items-center gap-2 text-xs"
								>
									<Pencil class="w-3 h-3 text-amber-600" />
									<span class="text-amber-700 font-medium">
										{{ formatHours(day.data.draftHours) }}h {{ translate("draft") }}
									</span>
								</div>
								<div v-if="day.data.logs.length > 0" class="text-xs text-gray-500 pt-1 border-t">
									{{ day.data.logs.length }} {{ translate("entries") }}
								</div>
							</div>

							<!-- Warning if no entries -->
							<div
								v-if="day.data.totalHours === 0 && day.date <= new Date()"
								class="mt-3 p-2 bg-red-50 border border-red-200 rounded-lg"
							>
								<p class="text-xs text-red-600 font-medium">
									{{ translate("No time logged") }}
								</p>
							</div>

							<!-- Success indicator -->
							<div
								v-if="day.data.totalHours >= 8"
								class="mt-3 p-2 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2"
							>
								<CheckCircle class="w-4 h-4 text-emerald-600" />
								<p class="text-xs text-emerald-700 font-medium">
									{{ translate("Goal reached!") }}
								</p>
							</div>
						</div>
					</div>

					<!-- Week summary -->
					<div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
						<div class="bg-blue-50 border border-blue-200 rounded-xl p-4">
							<p class="text-xs font-medium text-blue-700 uppercase">
								{{ translate("Week Total") }}
							</p>
							<p class="text-2xl font-bold text-blue-900 mt-1">
								{{ formatHours(weekDays.reduce((sum, d) => sum + d.data.totalHours, 0)) }}h
							</p>
							<p class="text-xs text-blue-600 mt-1">
								{{ translate("Target") }}: 40h
							</p>
						</div>
						<div class="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
							<p class="text-xs font-medium text-emerald-700 uppercase">
								{{ translate("Days Completed") }}
							</p>
							<p class="text-2xl font-bold text-emerald-900 mt-1">
								{{ weekDays.filter(d => d.data.totalHours >= 8).length }} / 5
							</p>
							<p class="text-xs text-emerald-600 mt-1">
								{{ translate("Working days") }}
							</p>
						</div>
						<div class="bg-amber-50 border border-amber-200 rounded-xl p-4">
							<p class="text-xs font-medium text-amber-700 uppercase">
								{{ translate("Average/Day") }}
							</p>
							<p class="text-2xl font-bold text-amber-900 mt-1">
								{{
									formatHours(
										weekDays.reduce((sum, d) => sum + d.data.totalHours, 0) / 7
									)
								}}h
							</p>
							<p class="text-xs text-amber-600 mt-1">
								{{ translate("This week") }}
							</p>
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
							<div class="md:col-span-2">
								<label class="text-xs font-medium text-gray-500">
									{{ translate("Project") }}
								</label>
								<select
									v-model="editForm.project"
									class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
								>
									<option value="">{{ translate("No project") }}</option>
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
							<div class="flex items-center gap-2 md:col-span-2">
								<input
									id="edit-timelog-is-billable"
									v-model="editForm.is_billable"
									type="checkbox"
									class="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
								/>
								<label for="edit-timelog-is-billable" class="text-sm text-gray-700">
									{{ translate("Is Billable") }}
								</label>
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

		<BackToDeskButton />
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

.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
