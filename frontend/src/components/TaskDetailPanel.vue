<script setup>
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from "vue";
import { useTaskStore } from "../stores/taskStore";
import QuickAddTask from "./QuickAddTask.vue";
import UserSelect from "./UserSelect.vue";
import TimeLogModal from "./TimeLogModal.vue?v=20241220-2030";
import dayjs from "dayjs";

import {
	X,
	ExternalLink,
	Calendar,
	User,
	Flag,
	Clock,
	CheckCircle2,
	Circle,
	AlertCircle,
	FileText,
	MessageSquare,
	Paperclip,
	ChevronDown,
	Plus,
	Trash2,
	Diamond,
	Folder,
} from "lucide-vue-next";
import { renderMarkdown } from "../utils/markdown";

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text) => {
	return typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
		? realWindow.__(text)
		: text;
};

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
});

const emit = defineEmits(["close"]);

const store = useTaskStore();

// Local editable state
const editableTask = ref({ ...props.task });
const isSaving = ref(false);
const activeTab = ref("details");
const showTimeLogModal = ref(false);
const timelogsLoading = ref(false);
const showMarkdownPreview = ref(false);

const descriptionMarkdownPreview = computed(() =>
	renderMarkdown(editableTask.value.description || "")
);

const descriptionPreviewButtonLabel = computed(() =>
	showMarkdownPreview.value
		? translate("Hide Markdown preview")
		: translate("Show Markdown preview")
);

const statusMenuOpen = ref(false);
const priorityMenuOpen = ref(false);
const showDuePresets = ref(false);
const statusMenuRef = ref(null);
const priorityMenuRef = ref(null);
const duePresetsRef = ref(null);
const dueLabelRef = ref(null);
const autosaveIndicatorVisible = ref(false);
let autosaveTimer = null;
const undoState = ref(null);
const redoState = ref(null);
let undoTimer = null;
let redoTimer = null;
const UNDO_WINDOW_MS = 5000;
const trackableFields = new Set(["status", "priority", "exp_end_date"]);

const COLLAPSE_KEY = "task-detail-panel-sections";
const defaultSectionState = {
	details: true,
	timeLog: false,
	subtasks: true,
};

function loadSectionStates() {
	if (typeof window === "undefined") {
		return { ...defaultSectionState };
	}
	try {
		const stored = window.localStorage.getItem(COLLAPSE_KEY);
		if (stored) {
			return { ...defaultSectionState, ...JSON.parse(stored) };
		}
	} catch (error) {
		console.error("Failed to load section state:", error);
	}
	return { ...defaultSectionState };
}

const sectionStates = ref(loadSectionStates());
const timeLogsFetched = ref(false);
const dueInputRef = ref(null);
const assigneeControlRef = ref(null);
const timeLogModalHours = ref(1);
const timeLogModalAutoFocus = ref(false);
const shortcutHighlight = ref(null);
let shortcutHighlightTimer = null;
const showDetailsSkeleton = computed(() => isSaving.value && sectionStates.value.details);
const showTimeLogSkeleton = computed(() => timelogsLoading.value && sectionStates.value.timeLog);
const dateValidationError = ref("");

watch(
	() => props.task,
	(newTask) => {
		editableTask.value = { ...newTask };
	},
	{ deep: true }
);

watch(
	() => [editableTask.value.exp_start_date, editableTask.value.exp_end_date],
	() => {
		validateDates();
	},
	{ immediate: true }
);

// Load metadata on mount
onMounted(() => {
	if (store.taskStatuses.length === 0) {
		store.fetchTaskStatuses();
	}
	if (store.taskPriorities.length === 0) {
		store.fetchTaskPriorities();
	}
});

const disabledStatuses = new Set(["Template"]);

const statusPalette = {
	Open: {
		icon: Circle,
		label: translate("Open"),
		bg: "bg-blue-50 border border-blue-200",
		text: "text-blue-700",
	},
	Working: {
		icon: Clock,
		label: translate("Working"),
		bg: "bg-blue-600 border border-blue-600",
		text: "text-white",
	},
	"Pending Review": {
		icon: AlertCircle,
		label: translate("Pending Review"),
		bg: "bg-purple-600 border border-purple-600",
		text: "text-white",
	},
	Completed: {
		icon: CheckCircle2,
		label: translate("Completed"),
		bg: "bg-emerald-600 border border-emerald-600",
		text: "text-white",
	},
	Overdue: {
		icon: AlertCircle,
		label: translate("Overdue"),
		bg: "bg-red-600 border border-red-600",
		text: "text-white",
	},
	Cancelled: {
		icon: Circle,
		label: translate("Cancelled"),
		bg: "bg-gray-100 border border-gray-200",
		text: "text-slate-500",
	},
};

const priorityPalette = {
	Low: {
		label: translate("Low"),
		bg: "bg-slate-100 border border-slate-200",
		text: "text-slate-700",
	},
	Medium: {
		label: translate("Medium"),
		bg: "bg-amber-100 border border-amber-200",
		text: "text-amber-700",
	},
	High: {
		label: translate("High"),
		bg: "bg-orange-100 border border-orange-200",
		text: "text-orange-700",
	},
	Urgent: {
		label: translate("Urgent"),
		bg: "bg-red-100 border border-red-200",
		text: "text-red-700",
	},
};

const statusOptions = computed(() =>
	store.taskStatuses.map((status) => ({
		value: status,
		palette: statusPalette[status] || statusPalette.Open,
		disabled: disabledStatuses.has(status),
	}))
);

const priorityOptions = computed(() =>
	store.taskPriorities.map((priority) => ({
		value: priority,
		palette: priorityPalette[priority] || priorityPalette.Medium,
	}))
);

const currentStatusPalette = computed(
	() => statusPalette[editableTask.value.status] || statusPalette.Open
);

const currentPriorityPalette = computed(
	() => priorityPalette[editableTask.value.priority] || priorityPalette.Medium
);

const statusCycleOrder = computed(() =>
	statusOptions.value.filter((opt) => !opt.disabled).map((opt) => opt.value)
);

const priorityCycleOrder = computed(() => priorityOptions.value.map((opt) => opt.value));

const duePresetOptions = computed(() => [
	{
		label: translate("Tomorrow"),
		getDate: () => dayjs().add(1, "day"),
	},
	{
		label: translate("In a week"),
		getDate: () => dayjs().add(7, "day"),
	},
	{
		label: translate("End of month"),
		getDate: () => dayjs().endOf("month"),
	},
]);

// Milestone handling
async function handleMilestoneChange(event) {
	const newMilestone = event.target.value || null;
	try {
		await store.assignTaskToMilestone(props.task.name, newMilestone);
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: newMilestone
					? translate("Task assigned to milestone")
					: translate("Task removed from milestone"),
				indicator: "green",
			});
		}
	} catch (error) {
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Failed to update milestone"),
				indicator: "red",
			});
		}
	}
}

// Project change handling
async function handleProjectChange() {
	const newProject = editableTask.value.project;
	if (newProject === props.task.project) return;

	try {
		await store.updateTask(props.task.name, { project: newProject });
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Task project changed"),
				indicator: "green",
			});
		}
	} catch (error) {
		editableTask.value.project = props.task.project;
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Failed to change project"),
				indicator: "red",
			});
		}
	}
}

function validateDates() {
	const start = editableTask.value.exp_start_date;
	const due = editableTask.value.exp_end_date;
	if (start && due && dayjs(due).isBefore(dayjs(start))) {
		dateValidationError.value = translate("Due Date cannot be before Start Date");
		return false;
	}
	dateValidationError.value = "";
	return true;
}

async function saveField(field, value, options = { trackUndo: true }) {
	const previousValue = props.task[field];
	if (value === previousValue) return;

	if (field === "exp_end_date" && !validateDates()) {
		return;
	}

	isSaving.value = true;
	try {
		await store.updateTask(props.task.name, { [field]: value });
		if (realWindow?.frappe && field === "exp_end_date") {
			realWindow.frappe.show_alert({
				message: translate("Date updated successfully"),
				indicator: "green",
			});
		}
		if (options.trackUndo && trackableFields.has(field)) {
			registerChange(field, previousValue, value);
		}
		showAutosaveFeedback();
	} catch (error) {
		// Revert on error
		editableTask.value[field] = previousValue;
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Failed to update field"),
				indicator: "red",
			});
		}
	} finally {
		isSaving.value = false;
	}
}

function showAutosaveFeedback() {
	autosaveIndicatorVisible.value = true;
	if (autosaveTimer) {
		clearTimeout(autosaveTimer);
	}
	autosaveTimer = setTimeout(() => {
		autosaveIndicatorVisible.value = false;
		autosaveTimer = null;
	}, 3000);
}

function registerChange(field, before, after) {
	if (!trackableFields.has(field)) return;
	if (before === after) return;

	undoState.value = {
		field,
		before,
		after,
		label: getFieldLabel(field),
	};
	redoState.value = null;
	clearUndoTimer();
	undoTimer = setTimeout(() => {
		undoState.value = null;
		undoTimer = null;
	}, UNDO_WINDOW_MS);
}

function clearUndoTimer() {
	if (undoTimer) {
		clearTimeout(undoTimer);
		undoTimer = null;
	}
}

function clearRedoTimer() {
	if (redoTimer) {
		clearTimeout(redoTimer);
		redoTimer = null;
	}
}

function getFieldLabel(field) {
	if (field === "status") return translate("Status");
	if (field === "priority") return translate("Priority");
	if (field === "exp_end_date") return translate("Due Date");
	return field;
}

function persistSectionStates() {
	if (typeof window === "undefined") return;
	window.localStorage.setItem(COLLAPSE_KEY, JSON.stringify(sectionStates.value));
}

async function ensureTimeLogsLoaded() {
	if (timeLogsFetched.value) return;
	try {
		await loadTimelogs();
		timeLogsFetched.value = true;
	} catch (error) {
		timeLogsFetched.value = false;
		throw error;
	}
}

function toggleSection(sectionKey) {
	sectionStates.value[sectionKey] = !sectionStates.value[sectionKey];
	persistSectionStates();
	if (sectionKey === "timeLog" && sectionStates.value.timeLog) {
		ensureTimeLogsLoaded();
	}
}

async function handleUndo() {
	if (!undoState.value) return;
	const { field, before, after } = undoState.value;
	clearUndoTimer();
	redoState.value = { field, before, after, label: getFieldLabel(field) };
	clearRedoTimer();
	redoTimer = setTimeout(() => {
		redoState.value = null;
		redoTimer = null;
	}, UNDO_WINDOW_MS);
	undoState.value = null;
	editableTask.value[field] = before;
	await saveField(field, before, { trackUndo: false });
}

async function handleRedo() {
	if (!redoState.value) return;
	const { field, after } = redoState.value;
	clearRedoTimer();
	redoState.value = null;
	editableTask.value[field] = after;
	await saveField(field, after, { trackUndo: false });
}

function toggleStatusMenu(event) {
	event.stopPropagation();
	statusMenuOpen.value = !statusMenuOpen.value;
	if (statusMenuOpen.value) {
		priorityMenuOpen.value = false;
	}
}

function togglePriorityMenu(event) {
	event.stopPropagation();
	priorityMenuOpen.value = !priorityMenuOpen.value;
	if (priorityMenuOpen.value) {
		statusMenuOpen.value = false;
	}
}

async function handleStatusSelection(option) {
	const newStatus = option.value;
	const progress = Number(editableTask.value.progress) || 0;
	if (newStatus === "Completed" && progress < 100) {
		const confirmed = window.confirm(
			translate("Progress is below 100%. Set it to 100% when marking as completed?")
		);
		if (!confirmed) {
			return;
		}
		editableTask.value.progress = 100;
		await saveField("progress", 100);
	}
	editableTask.value.status = newStatus;
	await saveField("status", newStatus);
	statusMenuOpen.value = false;
}

async function handlePrioritySelection(option) {
	editableTask.value.priority = option.value;
	await saveField("priority", option.value);
	priorityMenuOpen.value = false;
}

async function cycleStatus(direction = 1) {
	setShortcutHighlight("status");
	const options = statusCycleOrder.value;
	if (!options.length) return;
	const current = editableTask.value.status;
	const index = options.indexOf(current);
	const next = options[(index + direction + options.length) % options.length];
	if (next) {
		await handleStatusSelection({ value: next });
	}
}

async function cyclePriority(direction = 1) {
	setShortcutHighlight("priority");
	const options = priorityCycleOrder.value;
	if (!options.length) return;
	const current = editableTask.value.priority;
	const index = options.indexOf(current);
	const next = options[(index + direction + options.length) % options.length];
	if (next) {
		await handlePrioritySelection({ value: next });
	}
}

function toggleDuePresets(event) {
	if (event) {
		event.stopPropagation();
	}
	showDuePresets.value = !showDuePresets.value;
}

function handleDuePresetClick(preset) {
	const date = preset.getDate().format("YYYY-MM-DD");
	editableTask.value.exp_end_date = date;
	saveField("exp_end_date", date);
	showDuePresets.value = false;
}

function setShortcutHighlight(target) {
	shortcutHighlight.value = target;
	if (shortcutHighlightTimer) {
		clearTimeout(shortcutHighlightTimer);
	}
	shortcutHighlightTimer = setTimeout(() => {
		shortcutHighlight.value = null;
		shortcutHighlightTimer = null;
	}, 1300);
}

function openTimeLogModalWithPreset({ hours = 1, autoFocus = false } = {}) {
	timeLogModalHours.value = hours;
	timeLogModalAutoFocus.value = autoFocus;
	showTimeLogModal.value = true;
}

function closeTimeLogModal() {
	showTimeLogModal.value = false;
	timeLogModalAutoFocus.value = false;
}

function focusDueField() {
	setShortcutHighlight("due");
	nextTick(() => {
		if (dueInputRef.value) {
			dueInputRef.value.focus();
			showDuePresets.value = true;
		}
	});
}

function focusAssigneeField() {
	setShortcutHighlight("assignee");
	assigneeControlRef.value?.openDropdown?.();
}

function handleQuickTimeShortcut(hours) {
	setShortcutHighlight("time");
	openTimeLogModalWithPreset({ hours, autoFocus: true });
}

function shiftDueToTomorrow() {
	const newDate = dayjs().add(1, "day").format("YYYY-MM-DD");
	editableTask.value.exp_end_date = newDate;
	saveField("exp_end_date", newDate);
}

function markAsWorking() {
	const workingOption = statusOptions.value.find((opt) => opt.value === "Working");
	if (workingOption) {
		handleStatusSelection(workingOption);
	}
}

function handleDocumentClick(event) {
	if (
		statusMenuOpen.value &&
		statusMenuRef.value &&
		!statusMenuRef.value.contains(event.target)
	) {
		statusMenuOpen.value = false;
	}
	if (
		priorityMenuOpen.value &&
		priorityMenuRef.value &&
		!priorityMenuRef.value.contains(event.target)
	) {
		priorityMenuOpen.value = false;
	}
	if (
		showDuePresets.value &&
		duePresetsRef.value &&
		!duePresetsRef.value.contains(event.target) &&
		dueLabelRef.value &&
		!dueLabelRef.value.contains(event.target)
	) {
		showDuePresets.value = false;
	}
}

function handleGlobalKeydown(event) {
	const key = event.key?.toLowerCase();
	const tag = event.target?.tagName;
	const isInput =
		tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || event.target?.isContentEditable;

	if (!isInput && key === "s" && !event.metaKey && !event.ctrlKey) {
		event.preventDefault();
		cycleStatus(1);
		return;
	}

	if (!isInput && key === "p" && !event.metaKey && !event.ctrlKey) {
		event.preventDefault();
		cyclePriority(1);
		return;
	}

	if (!isInput && key === "d" && !event.metaKey && !event.ctrlKey) {
		event.preventDefault();
		focusDueField();
		return;
	}

	if (!isInput && key === "a" && !event.metaKey && !event.ctrlKey) {
		event.preventDefault();
		focusAssigneeField();
		return;
	}

	if (!isInput && key === "t" && !event.metaKey && !event.ctrlKey) {
		event.preventDefault();
		handleQuickTimeShortcut(0.25);
		return;
	}

	if ((event.metaKey || event.ctrlKey) && key === "s") {
		event.preventDefault();
		persistAllFields();
		return;
	}

	if (!isInput && (event.metaKey || event.ctrlKey) && key === "j") {
		event.preventDefault();
		setShortcutHighlight("time");
		openTimeLogModalWithPreset({ hours: 0.5, autoFocus: true });
		return;
	}

	if ((event.metaKey || event.ctrlKey) && key === "z" && !event.shiftKey) {
		event.preventDefault();
		handleUndo();
		return;
	}

	if ((event.metaKey || event.ctrlKey) && (key === "y" || (event.shiftKey && key === "z"))) {
		event.preventDefault();
		handleRedo();
		return;
	}
}

async function persistAllFields() {
	const fieldsToCheck = [
		"subject",
		"status",
		"priority",
		"exp_end_date",
		"exp_start_date",
		"progress",
		"description",
		"expected_time",
	];
	const updates = {};
	fieldsToCheck.forEach((field) => {
		const current = props.task[field];
		const rawUpdated = editableTask.value[field];
		const updated = rawUpdated === "" ? null : rawUpdated;
		if (updated === current) return;
		updates[field] = updated;
	});

	if (!validateDates()) {
		delete updates.exp_end_date;
	}

	if (!Object.keys(updates).length) {
		showAutosaveFeedback();
		return;
	}

	isSaving.value = true;
	try {
		const data = await store.updateTask(props.task.name, updates);
		if (data) {
			Object.assign(editableTask.value, data);
		}
		Object.entries(updates).forEach(([field, value]) => {
			const before = props.task[field];
			if (trackableFields.has(field)) {
				registerChange(field, before, value);
			}
		});
		showAutosaveFeedback();
	} catch (error) {
		console.error("Failed to persist fields:", error);
	} finally {
		isSaving.value = false;
	}
}

watch(
	() => sectionStates.value,
	() => {
		persistSectionStates();
	},
	{ deep: true }
);

watch(
	() => sectionStates.value.timeLog,
	(open) => {
		if (open) {
			ensureTimeLogsLoaded();
		}
	}
);

watch(
	() => props.task?.name,
	() => {
		timeLogsFetched.value = false;
		if (sectionStates.value.timeLog) {
			ensureTimeLogsLoaded();
		}
	}
);

function openInDesk() {
	realWindow?.open(`/app/task/${props.task.name}`, "_blank");
}

async function handleAddAssignee(user) {
	await store.assignTask(props.task.name, user, "add");
}

async function handleRemoveAssignee(user) {
	await store.assignTask(props.task.name, user, "remove");
}

onMounted(() => {
	store.fetchUsers();
	store.fetchAllProjects();
	document.addEventListener("click", handleDocumentClick);
	document.addEventListener("keydown", handleGlobalKeydown);
	if (sectionStates.value.timeLog) {
		ensureTimeLogsLoaded();
	}
});

onUnmounted(() => {
	document.removeEventListener("click", handleDocumentClick);
	document.removeEventListener("keydown", handleGlobalKeydown);
	if (autosaveTimer) {
		clearTimeout(autosaveTimer);
	}
	clearUndoTimer();
	clearRedoTimer();
	if (shortcutHighlightTimer) {
		clearTimeout(shortcutHighlightTimer);
		shortcutHighlightTimer = null;
	}
});

const currentTimelogs = computed(() => {
	return store.taskTimelogs[props.task.name] || { timelogs: [], total_hours: 0 };
});

async function loadTimelogs() {
	timelogsLoading.value = true;
	try {
		await store.fetchTaskTimelogs(props.task.name);
		return true;
	} catch (error) {
		console.error("Failed to load timelogs:", error);
		throw error;
	} finally {
		timelogsLoading.value = false;
	}
}

async function handleTimeLogSave(timelogData) {
	try {
		await store.createTimelog(timelogData);
		closeTimeLogModal();
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: "Time log saved successfully",
				indicator: "green",
			});
		}
	} catch (error) {
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({ message: "Failed to save time log", indicator: "red" });
		}
	}
}

async function handleDeleteTimelog(timelogName) {
	if (!confirm("Are you sure you want to delete this time log?")) return;

	try {
		await store.deleteTimelog(timelogName, props.task.name);
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({ message: "Time log deleted", indicator: "green" });
		}
	} catch (error) {
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: "Failed to delete time log",
				indicator: "red",
			});
		}
	}
}

function formatDate(dateStr) {
	if (!dateStr) return "";
	const date = new Date(dateStr);
	return date.toLocaleString("pl-PL", {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
}

async function handleSubtaskCreated() {
	// Refresh tasks and re-select current task to update children
	await store.fetchTasks(props.task.project);
	// Find updated task in store and re-select it
	const updatedTask = store.taskTree.find((t) => t.name === props.task.name);
	if (updatedTask) {
		store.selectTask(updatedTask);
	}
}
</script>

<template>
	<aside
		class="w-full max-w-[480px] md:min-w-[420px] bg-white border-l border-gray-200 flex flex-col flex-shrink-0 overflow-hidden"
	>
		<!-- Header -->
		<div class="sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
			<div class="flex items-center gap-2">
				<span class="text-sm font-medium text-gray-500">{{ task.name }}</span>
				<button
					@click="openInDesk"
					class="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
					title="Open in Desk"
				>
					<ExternalLink class="w-4 h-4" />
				</button>
			</div>
			<button @click="emit('close')" class="p-1 rounded hover:bg-gray-100 text-gray-500">
				<X class="w-5 h-5" />
			</button>
		</div>

		<!-- Content -->
		<div class="flex-1 overflow-y-auto">
			<div class="p-4 space-y-4">
				<section class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
				<header class="px-4 py-3 border-b border-gray-200">
					<button
						type="button"
						class="flex items-center justify-between w-full text-left text-sm font-semibold text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
						@click="toggleSection('details')"
						:aria-expanded="sectionStates.details"
						aria-controls="details-section"
					>
							<div class="flex items-center gap-2">
								<FileText class="w-4 h-4 text-blue-600" />
								<span>{{ translate("Details") }}</span>
							</div>
							<ChevronDown
								class="w-3 h-3 text-gray-400 transition-transform"
								:class="sectionStates.details ? 'rotate-180' : ''"
							/>
						</button>
					</header>
					<Transition name="fade">
						<div
							id="details-section"
							v-show="sectionStates.details"
							class="px-4 pb-4 pt-2 space-y-4 relative"
						>
							<div
								v-if="showDetailsSkeleton"
								class="absolute inset-0 z-10 flex items-center justify-center bg-white/80 backdrop-blur"
							>
								<div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
							</div>
							<div>
								<input
									v-model="editableTask.subject"
									type="text"
									class="w-full text-lg font-semibold text-gray-900 border-0 p-0 focus:ring-0 placeholder:text-gray-400"
									placeholder="Task name"
									@blur="saveField('subject', editableTask.subject)"
								/>
							</div>
							<div class="flex flex-wrap gap-3 text-[11px] text-gray-500">
								<span class="flex items-center gap-1">
									<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">S</kbd>
									<span>{{ translate("Cycle status") }}</span>
								</span>
								<span class="flex items-center gap-1">
									<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">P</kbd>
									<span>{{ translate("Cycle priority") }}</span>
								</span>
								<span class="flex items-center gap-1">
									<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">D</kbd>
									<span>{{ translate("Focus due date") }}</span>
								</span>
								<span class="flex items-center gap-1">
									<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">A</kbd>
									<span>{{ translate("Open assignees") }}</span>
								</span>
								<span class="flex items-center gap-1">
									<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">T</kbd>
									<span>{{ translate("Add 15m entry") }}</span>
								</span>
								<span class="flex items-center gap-1">
									<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">Ctrl+J</kbd>
									<span>{{ translate("Add 30m entry") }}</span>
								</span>
							</div>

							<div class="relative" ref="statusMenuRef">
								<label class="text-sm text-gray-500 mb-2 block">{{ translate("Status") }}</label>
								<button
									type="button"
									class="flex items-center gap-2 px-3 py-2 border rounded-lg text-sm w-full justify-between transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
									:class="[
										currentStatusPalette.bg,
										currentStatusPalette.text,
										shortcutHighlight === 'status' ? 'ring-2 ring-blue-400' : '',
									]"
									@click="toggleStatusMenu"
									:title="`${translate('Status')} (S)`"
								>
									<div class="flex items-center gap-2">
										<component
											:is="currentStatusPalette.icon"
											class="w-4 h-4"
										/>
										<span class="font-medium truncate">{{ currentStatusPalette.label }}</span>
									</div>
									<ChevronDown class="w-3 h-3 text-gray-400" />
								</button>
								<Transition name="menu-fade">
									<div
										v-if="statusMenuOpen"
										class="absolute z-10 mt-2 w-full rounded-md border border-gray-200 bg-white shadow-lg p-2 space-y-1"
									>
										<button
											v-for="opt in statusOptions"
											:key="opt.value"
											:disabled="opt.disabled"
											type="button"
											class="flex items-center gap-2 w-full px-3 py-2 text-left text-sm rounded-md transition-colors"
											:class="[
												opt.disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50',
												editableTask.status === opt.value ? opt.palette.bg : 'text-gray-600',
												editableTask.status === opt.value ? opt.palette.text : '',
											]"
											@click="handleStatusSelection(opt)"
										>
											<component
												:is="opt.palette.icon"
												class="w-4 h-4"
											/>
											{{ opt.palette.label }}
										</button>
									</div>
								</Transition>
							</div>

							<div class="relative" ref="priorityMenuRef">
								<label class="text-sm text-gray-500 mb-2 block flex items-center gap-1">
									<Flag class="w-3.5 h-3.5" />
									Priorytet
								</label>
								<button
									type="button"
									class="flex items-center gap-2 px-3 py-2 border rounded-lg text-sm w-full justify-between transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
									:class="[
										currentPriorityPalette.bg,
										currentPriorityPalette.text,
										shortcutHighlight === 'priority' ? 'ring-2 ring-blue-400' : '',
									]"
									@click="togglePriorityMenu"
									:title="`${translate('Priority')} (P)`"
								>
									<div class="flex items-center gap-2">
										<Flag class="w-4 h-4" />
										<span class="font-medium truncate">{{ currentPriorityPalette.label }}</span>
									</div>
									<ChevronDown class="w-3 h-3 text-gray-400" />
								</button>
								<Transition name="menu-fade">
									<div
										v-if="priorityMenuOpen"
										class="absolute z-10 mt-2 w-full rounded-md border border-gray-200 bg-white shadow-lg p-2 space-y-1"
									>
										<button
											v-for="opt in priorityOptions"
											:key="opt.value"
											type="button"
											class="flex items-center gap-2 w-full px-3 py-2 text-left text-sm rounded-md transition-colors"
											:class="[
												opt.palette.bg,
												opt.palette.text,
												editableTask.priority === opt.value ? 'shadow' : 'hover:bg-gray-50',
											]"
											@click="handlePrioritySelection(opt)"
										>
											<Flag class="w-4 h-4" />
											{{ opt.palette.label }}
										</button>
									</div>
								</Transition>
							</div>

							<div class="flex items-center gap-3">
								<label class="text-sm text-gray-500 w-20 flex items-center gap-1">
									<Diamond class="w-3 h-3" />
									{{ translate("Milestone") }}
								</label>
								<select
									:value="task.milestone || ''"
									@change="handleMilestoneChange"
									class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								>
									<option value="">{{ translate("No milestone") }}</option>
									<option
										v-for="milestone in store.milestones"
										:key="milestone.name"
										:value="milestone.name"
									>
										{{ milestone.milestone_name }}
									</option>
								</select>
							</div>

							<div class="flex items-center gap-3">
								<label class="text-sm text-gray-500 w-20 flex items-center gap-1">
									<Folder class="w-3 h-3" />
									{{ translate("Project") }}
								</label>
								<select
									v-model="editableTask.project"
									@change="handleProjectChange"
									class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								>
									<option
										v-for="proj in store.allProjects"
										:key="proj.name"
										:value="proj.name"
									>
										{{ proj.project_name }}
									</option>
								</select>
							</div>

							<div class="flex items-start gap-3">
								<label class="text-sm text-gray-500 w-20 pt-2">{{
									translate("Assigned")
								}}</label>
								<div
									class="flex-1 transition focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-1"
									:class="shortcutHighlight === 'assignee' ? 'ring-2 ring-blue-400 rounded-md' : ''"
									:title="`A — ${translate('Assign user...')}`"
								>
									<UserSelect
										ref="assigneeControlRef"
										:model-value="task._assign"
										:placeholder="translate('Assign user...')"
										@add="handleAddAssignee"
										@remove="handleRemoveAssignee"
									/>
								</div>
							</div>

					<div class="flex items-center gap-3 relative">
						<button
							type="button"
							ref="dueLabelRef"
							class="text-sm text-gray-500 w-20 text-left hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
							@click="toggleDuePresets"
							:aria-expanded="showDuePresets"
							aria-controls="due-presets-panel"
							aria-haspopup="listbox"
							:title="`${translate('Due Date')} (D)`"
						>
							{{ translate("Due Date") }}
						</button>
						<div
							class="flex-1 relative"
							:class="shortcutHighlight === 'due' ? 'ring-2 ring-blue-400 rounded-md' : ''"
						>
							<input
								ref="dueInputRef"
								v-model="editableTask.exp_end_date"
								type="date"
								@change="saveField('exp_end_date', editableTask.exp_end_date)"
								class="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
							/>
							<Transition name="menu-fade">
								<div
									v-if="showDuePresets"
									ref="duePresetsRef"
									id="due-presets-panel"
									class="absolute z-10 left-0 top-full mt-2 w-56 rounded-md border border-gray-200 bg-white shadow-lg p-2 space-y-1"
									@click.stop
								>
									<button
										v-for="preset in duePresetOptions"
										:key="preset.label"
										type="button"
										class="w-full text-left px-3 py-2 text-sm rounded-md hover:bg-gray-50"
										@click="handleDuePresetClick(preset)"
									>
										{{ preset.label }}
									</button>
								</div>
							</Transition>
						</div>
						<span class="text-xs text-gray-400">
							<kbd class="px-1 border border-gray-200 rounded">Ctrl</kbd>+<kbd class="px-1 border border-gray-200 rounded">S</kbd>
						</span>
					</div>
					<div v-if="dateValidationError" class="px-4 text-xs text-red-600">
						{{ dateValidationError }}
					</div>
					<div
						v-if="props.task.is_overdue"
						class="flex flex-wrap items-center gap-2 px-4 text-xs text-blue-600"
					>
						<button
							type="button"
							class="px-2 py-1 font-medium rounded border border-blue-100 bg-blue-50"
							@click="shiftDueToTomorrow"
						>
							{{ translate("Przesuń termin") }}
						</button>
						<button
							type="button"
							class="px-2 py-1 font-medium rounded border border-blue-100 bg-blue-50"
							@click="markAsWorking"
						>
							{{ translate("Oznacz jako w toku") }}
						</button>
					</div>

							<div class="flex items-center gap-3">
								<label class="text-sm text-gray-500 w-20">{{ translate("Expected Time") }}</label>
								<input
									v-model.number="editableTask.expected_time"
									type="number"
									min="0"
									step="0.25"
									@blur="saveField('expected_time', editableTask.expected_time)"
									class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
									:placeholder="translate('e.g. 4')"
								/>
							</div>

							<div class="flex items-center gap-3">
								<label class="text-sm text-gray-500 w-20">{{ translate("Start Date") }}</label>
								<input
									v-model="editableTask.exp_start_date"
									type="date"
									@change="saveField('exp_start_date', editableTask.exp_start_date)"
									class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								/>
							</div>

							<div class="flex items-center gap-3">
								<label class="text-sm text-gray-500 w-20">{{ translate("Progress") }}</label>
								<div class="flex-1 flex items-center gap-2">
									<input
										v-model.number="editableTask.progress"
										type="range"
										min="0"
										max="100"
										@change="saveField('progress', editableTask.progress)"
										class="flex-1"
									/>
									<span class="text-sm text-gray-600 w-10 text-right">
										{{ editableTask.progress || 0 }}%
									</span>
								</div>
							</div>

							<div>
								<div class="flex items-center justify-between">
									<label class="text-sm font-medium text-gray-700 mb-2 block">{{
										translate("Description")
									}}</label>
									<button
										type="button"
										@click="showMarkdownPreview = !showMarkdownPreview"
										class="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
									>
										{{ descriptionPreviewButtonLabel }}
									</button>
								</div>
								<textarea
									v-model="editableTask.description"
									rows="4"
									class="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
									:placeholder="translate('Add description...')"
									@blur="saveField('description', editableTask.description)"
								></textarea>
								<div
									v-if="showMarkdownPreview"
									class="mt-2 rounded-md border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700 shadow-sm whitespace-pre-wrap break-words"
									v-html="descriptionMarkdownPreview"
								></div>
							</div>
						</div>
					</Transition>
				</section>

				<section class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
					<header class="px-4 py-3 border-b border-gray-200">
						<button
							type="button"
							class="flex items-center justify-between w-full text-left text-sm font-semibold text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
							@click="toggleSection('timeLog')"
							:aria-expanded="sectionStates.timeLog"
							aria-controls="time-log-section"
						>
							<div class="flex items-center gap-2">
								<Clock class="w-4 h-4 text-blue-600" />
								<span>{{ translate("Time Log") }}</span>
								<span v-if="currentTimelogs.total_hours > 0" class="text-xs text-gray-500">
									({{ currentTimelogs.total_hours.toFixed(2) }} hrs)
								</span>
							</div>
							<ChevronDown
								class="w-3 h-3 text-gray-400 transition-transform"
								:class="sectionStates.timeLog ? 'rotate-180' : ''"
							/>
						</button>
					</header>
					<Transition name="fade">
						<div
							id="time-log-section"
							v-show="sectionStates.timeLog"
							class="px-4 pb-4 pt-3 space-y-4 relative"
						>
							<div
								v-if="showTimeLogSkeleton"
								class="absolute inset-0 z-10 flex items-center justify-center bg-white/80 backdrop-blur"
							>
								<div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
							</div>
							<div class="flex items-center justify-between">
								<div>
									<h3 class="text-sm font-medium text-gray-700">
										{{ translate("Time Log") }}
									</h3>
									<p
										v-if="currentTimelogs.total_hours > 0"
										class="text-xs text-gray-500 mt-0.5"
									>
										{{ translate("Total") }}:
										{{ currentTimelogs.total_hours.toFixed(2) }}
										{{ translate("hrs") }}.
									</p>
								</div>
								<button
									type="button"
									@click="openTimeLogModalWithPreset({ hours: 1, autoFocus: true })"
									:title="`${translate('Add time')} (T / Ctrl+J)`"
									:class="[
										'flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
										shortcutHighlight === 'time' ? 'ring-2 ring-blue-400' : '',
									]"
								>
									<Plus class="w-3.5 h-3.5" />
									{{ translate("Add time") }}
								</button>
							</div>

							<div v-if="timelogsLoading" class="text-center py-4">
								<div
									class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"
								></div>
							</div>

							<div
								v-else-if="currentTimelogs.timelogs.length === 0"
								class="text-sm text-gray-500 text-center py-4"
							>
								{{ translate("No time entries") }}
							</div>

							<div v-else class="space-y-2">
								<div
									v-for="log in currentTimelogs.timelogs"
									:key="log.timelog_name"
									class="bg-gray-50 rounded-md p-3 text-sm relative"
								>
									<div class="flex items-start justify-between gap-2">
										<div class="flex-1">
											<div class="flex items-center gap-2 mb-1">
												<Clock class="w-3.5 h-3.5 text-blue-600" />
												<span class="font-semibold text-gray-900"
													>{{ log.hours }} hrs</span
												>
												<span class="text-xs text-gray-500">{{
													log.activity_type
												}}</span>
												<span
													v-if="log.status"
													:class="[
														'px-2 py-0.5 rounded-full text-xs font-medium',
														log.status === 'Submitted'
															? 'bg-green-100 text-green-800'
															: log.status === 'Billed'
															? 'bg-blue-100 text-blue-800'
															: log.status === 'Draft'
															? 'bg-gray-100 text-gray-800'
															: 'bg-gray-100 text-gray-800',
													]"
												>
													{{ log.status }}
												</span>
											</div>
											<p v-if="log.description" class="text-gray-600 text-xs mb-1">
												{{ log.description }}
											</p>
											<div class="flex items-center gap-2 text-xs text-gray-500">
												<span>{{ log.user_full_name }}</span>
												<span>•</span>
												<span>{{ formatDate(log.from_time) }}</span>
											</div>
										</div>
										<button
											@click="handleDeleteTimelog(log.timelog_name)"
											class="p-1 rounded hover:bg-red-100 text-gray-400 hover:text-red-600"
											title="Delete time log"
										>
											<Trash2 class="w-3.5 h-3.5" />
										</button>
									</div>
								</div>
							</div>
						</div>
					</Transition>
				</section>

				<section class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
					<header class="px-4 py-3 border-b border-gray-200">
						<button
							type="button"
							class="flex items-center justify-between w-full text-left text-sm font-semibold text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
							@click="toggleSection('subtasks')"
							:aria-expanded="sectionStates.subtasks"
							aria-controls="subtasks-section"
						>
							<div class="flex items-center gap-2">
								<Folder class="w-4 h-4 text-blue-600" />
								<span>{{ translate("Subtasks") }}</span>
							</div>
							<ChevronDown
								class="w-3 h-3 text-gray-400 transition-transform"
								:class="sectionStates.subtasks ? 'rotate-180' : ''"
							/>
						</button>
					</header>
					<Transition name="fade">
						<div
							id="subtasks-section"
							v-show="sectionStates.subtasks"
							class="px-4 pb-4 pt-3 space-y-3"
						>
							<div v-if="task.children?.length > 0" class="space-y-1 mb-2">
								<div
									v-for="child in task.children"
									:key="child.name"
									class="flex items-center gap-2 text-sm text-gray-600 py-1"
								>
									<component
										:is="child.status === 'Completed' ? CheckCircle2 : Circle"
										:class="[
											'w-4 h-4',
											child.status === 'Completed'
												? 'text-green-500'
												: 'text-gray-400',
										]"
									/>
									<span
										:class="{
											'line-through text-gray-400': child.status === 'Completed',
										}"
									>
										{{ child.subject }}
									</span>
								</div>
							</div>
							<QuickAddTask
								:project-id="task.project"
								:parent-task="task.name"
								placeholder="Dodaj podzadanie..."
								@created="handleSubtaskCreated"
							/>
						</div>
					</Transition>
				</section>
			</div>
		</div>

		<div
			v-if="undoState || redoState"
			class="border-t border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-600 flex items-center justify-between"
		>
			<div>
				<span v-if="undoState">
					{{ translate("Undo") }} {{ undoState.label }}
				</span>
				<span v-else>
					{{ translate("Redo") }} {{ redoState.label }}
				</span>
			</div>
			<div class="flex gap-2">
				<button
					v-if="undoState"
					type="button"
					class="px-2 py-1 text-xs text-blue-600 rounded-md border border-blue-100 hover:bg-blue-50"
					@click="handleUndo"
				>
					{{ translate("Undo") }}
				</button>
				<button
					v-else
					type="button"
					class="px-2 py-1 text-xs text-blue-600 rounded-md border border-blue-100 hover:bg-blue-50"
					@click="handleRedo"
				>
					{{ translate("Redo") }}
				</button>
			</div>
		</div>

		<!-- Footer -->
		<div class="border-t border-gray-200 px-4 py-3">
			<div class="flex items-center justify-between text-xs text-gray-500">
				<div class="flex items-center gap-3">
					<span v-if="task.creation">Utworzono {{ task.creation }}</span>
					<span
						v-if="autosaveIndicatorVisible"
						class="text-emerald-600 flex items-center gap-1 font-semibold"
					>
						<span aria-hidden="true">✓</span>
						Zapisano
					</span>
				</div>
				<span v-if="isSaving" class="text-blue-600">Zapisywanie...</span>
			</div>
		</div>

		<!-- Time Log Modal -->
		<TimeLogModal
			:task="task"
			:show="showTimeLogModal"
			:default-hours="timeLogModalHours"
			:auto-focus="timeLogModalAutoFocus"
			@close="closeTimeLogModal"
			@save="handleTimeLogSave"
		/>
	</aside>
</template>

<style scoped>
.menu-fade-enter-active,
.menu-fade-leave-active {
	transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
	opacity: 0;
	transform: translateY(-4px);
}
</style>
