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
	Maximize2,
	Minimize2,
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
	Info,
	Image,
	Upload,
} from "lucide-vue-next";
import { TextEditor, useFileUpload } from "frappe-ui";
import { renderMarkdown } from "../utils/markdown";

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text) => {
	return typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
		? realWindow.__(text)
		: text;
};

const isTouchDevice = computed(() => {
	return Boolean(realWindow?.matchMedia?.("(hover: none)").matches);
});

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
const showShortcutsInfo = ref(false);
const shortcutsInfoRef = ref(null);

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

const COLLAPSE_KEY = "task-detail-panel-sections";
const defaultSectionState = {
	details: true,
	timeLog: false,
	subtasks: true,
	attachments: false,
	comments: false,
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
const attachments = ref([]);
const attachmentsLoading = ref(false);
const attachmentsFetched = ref(false);
const comments = ref([]);
const commentsLoading = ref(false);
const commentsFetched = ref(false);
const commentText = ref("");
const commentMentions = ref([]);
const commentEditorRef = ref(null);
const commentSubmitting = ref(false);
const commentHasContent = computed(() => stripHtml(commentText.value).length > 0);
const uploadProgress = ref(0);
const isUploading = ref(false);
const fileInputRef = ref(null);
const isDragOver = ref(false);
const dueInputRef = ref(null);
const assigneeControlRef = ref(null);
const timeLogModalHours = ref(1);
const timeLogModalAutoFocus = ref(false);
const shortcutHighlight = ref(null);
let shortcutHighlightTimer = null;
const showDetailsSkeleton = computed(() => isSaving.value && sectionStates.value.details);
const showTimeLogSkeleton = computed(() => timelogsLoading.value && sectionStates.value.timeLog);
const dateValidationError = ref("");
const isFullscreen = ref(false);

watch(
	() => props.task,
	(newTask) => {
		editableTask.value = { ...newTask };
		attachmentsFetched.value = false;
		attachments.value = [];
		commentsFetched.value = false;
		comments.value = [];
		commentText.value = "";
		commentMentions.value = [];
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

watch(
	() => sectionStates.value.comments,
	(isOpen) => {
		if (isOpen) {
			ensureCommentsLoaded();
		}
	}
);

// Load metadata on mount
onMounted(() => {
	if (store.taskStatuses.length === 0) {
		store.fetchTaskStatuses();
	}
	if (store.taskPriorities.length === 0) {
		store.fetchTaskPriorities();
	}
	fetchCommentMentions();
});

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
		bg: "bg-green-600 border border-green-600",
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
	store.taskStatuses
		.filter((status) => status !== "Template")
		.map((status) => ({
			value: status,
			palette: statusPalette[status] || statusPalette.Open,
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

const directSubtasks = computed(() => {
	return store.tasks
		.filter((item) => item.parent_task === props.task.name)
		.sort((a, b) => (a.idx || 0) - (b.idx || 0));
});

const statusCycleOrder = computed(() => statusOptions.value.map((opt) => opt.value));

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
	const previousMilestone = editableTask.value.milestone;

	// Update local state immediately for UI feedback
	editableTask.value.milestone = newMilestone;

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
		// Revert on error
		editableTask.value.milestone = previousMilestone;
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

	async function saveField(field, value) {
		const previousValue = props.task[field];
		if (value === previousValue) return;

		if (field === "exp_end_date" && !validateDates()) {
			return;
		}

		isSaving.value = true;
		let previousStatus = null;
		let statusChanged = false;
		try {
			const updates = { [field]: value };

			// Jeśli zmieniamy datę realizacji dla zadania ze statusem "Overdue"
			// i nowa data nie jest w przeszłości, zmień status na "Open"
			if (field === "exp_end_date" && props.task.status === "Overdue" && value) {
				const today = dayjs().startOf("day");
				const newDueDate = dayjs(value).startOf("day");

				if (!newDueDate.isBefore(today)) {
					updates.status = "Open";
					previousStatus = editableTask.value.status;
					statusChanged = true;
					editableTask.value.status = "Open";
					if (realWindow?.frappe) {
						realWindow.frappe.show_alert({
							message: translate("Status changed to Open because new due date is not in the past"),
							indicator: "blue",
						});
					}
				}
			}

			await store.updateTask(props.task.name, updates);
			if (realWindow?.frappe && field === "exp_end_date") {
				realWindow.frappe.show_alert({
					message: translate("Date updated successfully"),
					indicator: "green",
				});
			}
			showAutosaveFeedback();
		} catch (error) {
			// Revert on error
			editableTask.value[field] = previousValue;
			if (statusChanged) {
				editableTask.value.status = previousStatus;
			}
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

function handleActualDateBlur(field) {
	saveField(field, editableTask.value[field]);
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
	if (
		showShortcutsInfo.value &&
		shortcutsInfoRef.value &&
		!shortcutsInfoRef.value.contains(event.target)
	) {
		showShortcutsInfo.value = false;
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
		persistAllFields();
		return;
	}

	if (key === "escape" && showShortcutsInfo.value) {
		showShortcutsInfo.value = false;
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
	() => sectionStates.value.attachments,
	(open) => {
		if (open) {
			ensureAttachmentsLoaded();
		}
	}
);

watch(
	() => props.task?.name,
	() => {
		timeLogsFetched.value = false;
		attachmentsFetched.value = false;
		attachments.value = [];
		commentsFetched.value = false;
		comments.value = [];
		commentText.value = "";
		if (sectionStates.value.timeLog) {
			ensureTimeLogsLoaded();
		}
		if (sectionStates.value.attachments) {
			ensureAttachmentsLoaded();
		}
		if (sectionStates.value.comments) {
			ensureCommentsLoaded();
		}
	}
);

function openInDesk() {
	realWindow?.open(`/app/task/${props.task.name}`, "_blank");
}

function toggleFullscreen() {
	isFullscreen.value = !isFullscreen.value;
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
	if (sectionStates.value.attachments) {
		ensureAttachmentsLoaded();
	}
});

	onUnmounted(() => {
		document.removeEventListener("click", handleDocumentClick);
		document.removeEventListener("keydown", handleGlobalKeydown);
		if (autosaveTimer) {
			clearTimeout(autosaveTimer);
		}
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

// ── Attachments ──────────────────────────────────────────────

function getCsrfToken() {
	if (realWindow?.frappe?.csrf_token && realWindow.frappe.csrf_token !== "None") {
		return realWindow.frappe.csrf_token;
	}
	if (realWindow?.csrf_token && realWindow.csrf_token !== "{{ csrf_token }}") {
		return realWindow.csrf_token;
	}
	return "";
}

async function attachmentApiCall(method, params = {}) {
	const formData = new FormData();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined) {
			formData.append(key, value);
		}
	});
	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: { "X-Frappe-CSRF-Token": getCsrfToken() },
		body: formData,
	});
	const data = await response.json();
	if (data.exc) throw new Error(data._server_messages || "API error");
	return data.message;
}

async function fetchAttachments() {
	attachmentsLoading.value = true;
	try {
		attachments.value = await attachmentApiCall(
			"erpnext_projekt_hub.api.project_hub.get_task_attachments",
			{ task_name: props.task.name }
		);
	} catch (error) {
		console.error("Failed to load attachments:", error);
	} finally {
		attachmentsLoading.value = false;
	}
}

function stripHtml(html) {
	if (!html) return "";
	return String(html).replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function handleCommentChange(value) {
	commentText.value = value || "";
}

async function fetchComments() {
	commentsLoading.value = true;
	try {
		comments.value = await attachmentApiCall(
			"erpnext_projekt_hub.api.project_hub.get_task_comments",
			{ task_name: props.task.name }
		);
	} catch (error) {
		console.error("Failed to load comments:", error);
	} finally {
		commentsLoading.value = false;
	}
}

async function fetchCommentMentions() {
	try {
		commentMentions.value = (await attachmentApiCall(
			"frappe.desk.search.get_names_for_mentions",
			{ search_term: "" }
		)) || [];
	} catch (error) {
		console.error("Failed to load comment mentions:", error);
		commentMentions.value = [];
	}
}

function ensureCommentsLoaded() {
	if (!commentsFetched.value) {
		commentsFetched.value = true;
		fetchComments();
	}
}

function ensureAttachmentsLoaded() {
	if (!attachmentsFetched.value) {
		attachmentsFetched.value = true;
		fetchAttachments();
	}
}

function isImageFile(file) {
	return /^(jpg|jpeg|png|gif|webp|svg|bmp)$/i.test(file.file_type || "");
}

function formatFileSize(bytes) {
	if (!bytes) return "";
	if (bytes < 1024) return bytes + " B";
	if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
	return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function triggerFileInput() {
	fileInputRef.value?.click();
}

async function handleFileSelect(event) {
	const files = event.target.files;
	if (!files?.length) return;
	await uploadFiles(files);
	event.target.value = "";
}

function handleDragOver(event) {
	event.preventDefault();
	isDragOver.value = true;
}

function handleDragLeave() {
	isDragOver.value = false;
}

async function handleDrop(event) {
	event.preventDefault();
	isDragOver.value = false;
	const files = event.dataTransfer?.files;
	if (!files?.length) return;
	await uploadFiles(files);
}

async function uploadFiles(files) {
	isUploading.value = true;
	uploadProgress.value = 0;
	const total = files.length;
	let completed = 0;
	const uploader = useFileUpload();

	try {
		for (const file of files) {
			const isImage = file?.type?.startsWith("image/");
			await uploader.upload(file, {
				doctype: "Task",
				docname: props.task.name,
				optimize: isImage,
				...(isImage ? { max_width: 1920, max_height: 1920 } : {}),
			});
			completed++;
			uploadProgress.value = Math.round((completed / total) * 100);
		}

		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: total === 1 ? "Plik dodany" : `Dodano ${total} plików`,
				indicator: "green",
			});
		}

		await fetchAttachments();
	} catch (error) {
		console.error("Upload failed:", error);
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: error?.message || "Nie udało się przesłać pliku",
				indicator: "red",
			});
		}
	} finally {
		isUploading.value = false;
		uploadProgress.value = 0;
	}
}

async function submitComment() {
	const editor = commentEditorRef.value?.editor;
	const content = editor?.getHTML?.().trim?.() || commentText.value.trim();
	if (!content || commentSubmitting.value) return;

	commentSubmitting.value = true;
	try {
		await attachmentApiCall("erpnext_projekt_hub.api.project_hub.add_task_comment", {
			task_name: props.task.name,
			content,
		});
		commentText.value = "";
		if (editor?.commands?.setContent) {
			editor.commands.setContent("");
		}
		await fetchComments();
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Comment added"),
				indicator: "green",
			});
		}
	} catch (error) {
		console.error("Failed to add comment:", error);
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: error?.message || translate("Failed to add comment"),
				indicator: "red",
			});
		}
	} finally {
		commentSubmitting.value = false;
	}
}

async function deleteAttachment(fileName) {
	if (!confirm(translate("Are you sure you want to delete this attachment?"))) return;

	try {
		await attachmentApiCall(
			"erpnext_projekt_hub.api.project_hub.delete_task_attachment",
			{ file_name: fileName }
		);
		attachments.value = attachments.value.filter((f) => f.name !== fileName);
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({ message: "Załącznik usunięty", indicator: "green" });
		}
	} catch (error) {
		console.error("Failed to delete attachment:", error);
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: "Nie udało się usunąć załącznika",
				indicator: "red",
			});
		}
	}
}
</script>

<template>
	<aside
		:class="[
			'w-full bg-white border-l border-gray-200 flex flex-col flex-shrink-0 overflow-hidden',
			isFullscreen ? 'max-w-full md:min-w-full' : 'max-w-full sm:max-w-[480px] md:min-w-[420px]',
		]"
	>
		<!-- Header -->
		<div class="sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
			<div class="flex items-center gap-2">
				<span class="text-sm font-medium text-gray-500">{{ task.name }}</span>
			</div>
			<div class="flex items-center gap-2">
				<button
					v-if="!isTouchDevice"
					type="button"
					class="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
					@click="toggleFullscreen"
					:title="isFullscreen ? translate('Exit fullscreen') : translate('Fullscreen')"
				>
					<component :is="isFullscreen ? Minimize2 : Maximize2" class="w-4 h-4" />
				</button>
				<button
					type="button"
					@click="openInDesk"
					class="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 flex items-center gap-1 text-xs font-medium"
				>
					<ExternalLink class="w-4 h-4" />
					<span class="hidden md:inline">{{ translate("Open full window") }}</span>
				</button>
				<button
					type="button"
					@click="emit('close')"
					class="p-1 rounded hover:bg-gray-100 text-gray-500"
					:title="translate('Close')"
				>
					<X class="w-5 h-5" />
				</button>
			</div>
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
							<div v-if="!isTouchDevice" class="flex items-center justify-between text-[11px] text-gray-500">
								<span>{{ translate("Keyboard shortcuts") }}</span>
								<div class="relative" ref="shortcutsInfoRef">
									<button
										type="button"
										class="inline-flex items-center justify-center h-7 w-7 rounded-full border border-gray-200 bg-gray-50 text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
										:aria-expanded="showShortcutsInfo"
										:aria-label="translate('Keyboard shortcuts')"
										@click="showShortcutsInfo = !showShortcutsInfo"
									>
										<Info class="w-4 h-4" />
									</button>
									<Transition name="menu-fade">
										<div
											v-if="showShortcutsInfo"
											class="absolute right-0 mt-2 w-72 max-w-[90vw] rounded-lg border border-gray-200 bg-white shadow-lg p-3 text-xs text-gray-700 z-20"
										>
											<div class="flex items-center justify-between mb-2">
												<span class="font-semibold text-gray-900">
													{{ translate("Keyboard shortcuts") }}
												</span>
												<button
													type="button"
													class="text-gray-400 hover:text-gray-600"
													:aria-label="translate('Close dialog')"
													@click="showShortcutsInfo = false"
												>
													<X class="w-3.5 h-3.5" />
												</button>
											</div>
											<div class="space-y-2">
												<div class="flex items-center justify-between gap-3">
													<span>{{ translate("Cycle status") }}</span>
													<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">S</kbd>
												</div>
												<div class="flex items-center justify-between gap-3">
													<span>{{ translate("Cycle priority") }}</span>
													<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">P</kbd>
												</div>
												<div class="flex items-center justify-between gap-3">
													<span>{{ translate("Focus due date") }}</span>
													<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">D</kbd>
												</div>
												<div class="flex items-center justify-between gap-3">
													<span>{{ translate("Open assignees") }}</span>
													<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">A</kbd>
												</div>
												<div class="flex items-center justify-between gap-3">
													<span>{{ translate("Add 15m entry") }}</span>
													<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">T</kbd>
												</div>
												<div class="flex items-center justify-between gap-3">
													<span>{{ translate("Add 30m entry") }}</span>
													<kbd class="px-1.5 py-0.5 border border-gray-300 bg-gray-50 rounded text-[10px] font-semibold uppercase">Ctrl+J</kbd>
												</div>
											</div>
										</div>
									</Transition>
								</div>
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
											type="button"
											class="flex items-center gap-2 w-full px-3 py-2 text-left text-sm rounded-md transition-colors"
											:class="[
												'hover:bg-gray-50',
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

							<div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-3">
								<label class="text-sm text-gray-500 sm:w-20 flex items-center gap-1">
									<Diamond class="w-3 h-3" />
									{{ translate("Milestone") }}
								</label>
								<select
									:value="editableTask.milestone || ''"
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

							<div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-3">
								<label class="text-sm text-gray-500 sm:w-20 flex items-center gap-1">
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

							<div class="flex flex-col sm:flex-row sm:items-start gap-1.5 sm:gap-3">
								<label class="text-sm text-gray-500 sm:w-20 sm:pt-2">{{
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

					<div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-3 relative">
						<button
							type="button"
							ref="dueLabelRef"
							class="text-sm text-gray-500 sm:w-20 text-left hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
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
								@blur="handleActualDateBlur('exp_end_date')"
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

							<div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-3">
								<label class="text-sm text-gray-500 sm:w-20">{{ translate("Expected Time") }}</label>
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

							<div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-3">
								<label class="text-sm text-gray-500 sm:w-20">{{ translate("Start Date") }}</label>
								<input
									v-model="editableTask.exp_start_date"
									type="date"
									@blur="handleActualDateBlur('exp_start_date')"
									class="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								/>
							</div>

							<div class="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-3">
								<label class="text-sm text-gray-500 sm:w-20">{{ translate("Progress") }}</label>
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
							@click="toggleSection('comments')"
							:aria-expanded="sectionStates.comments"
							aria-controls="comments-section"
						>
							<div class="flex items-center gap-2">
								<MessageSquare class="w-4 h-4 text-blue-600" />
								<span>{{ translate("Comments") }}</span>
								<span v-if="comments.length > 0" class="text-xs text-gray-500">
									({{ comments.length }})
								</span>
							</div>
							<ChevronDown
								class="w-3 h-3 text-gray-400 transition-transform"
								:class="sectionStates.comments ? 'rotate-180' : ''"
							/>
						</button>
					</header>
					<Transition name="fade">
						<div id="comments-section" v-show="sectionStates.comments" class="px-4 pb-4 pt-3 space-y-3">
							<div class="space-y-2">
								<label class="block text-sm font-medium text-gray-700">
									{{ translate("Add a comment") }}
								</label>
								<TextEditor
									ref="commentEditorRef"
									:content="commentText"
									@change="handleCommentChange"
									:editable="true"
									:mentions="commentMentions"
									:placeholder="() => translate('Type your comment...')"
									editor-class="min-h-[120px] rounded-md border border-gray-300 bg-white text-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500"
								/>
								<div class="flex justify-end">
									<button
										type="button"
										@click="submitComment"
										:disabled="commentSubmitting || !commentHasContent"
										class="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
									>
										<span v-if="commentSubmitting" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
										{{ translate("Post Comment") }}
									</button>
								</div>
							</div>

							<div v-if="commentsLoading" class="text-center py-4">
								<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
							</div>

							<div v-else-if="comments.length === 0" class="text-sm text-gray-500 text-center py-4">
								{{ translate("No comments yet") }}
							</div>

								<div v-else class="space-y-3">
									<div
										v-for="comment in comments"
										:key="comment.name"
										class="rounded-lg border border-gray-200 bg-gray-50 p-3"
									>
									<div class="flex items-center justify-between gap-3 mb-2">
										<div class="text-xs font-medium text-gray-700">
											{{ comment.comment_by || comment.owner }}
										</div>
										<div class="text-xs text-gray-500">
											{{ comment.creation }}
										</div>
									</div>
										<div class="text-sm text-gray-700 whitespace-pre-wrap" v-html="comment.content"></div>
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
							<div v-if="directSubtasks.length > 0" class="space-y-1 mb-2">
								<div
									v-for="child in directSubtasks"
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

				<!-- Attachments section -->
				<section class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
					<header class="px-4 py-3 border-b border-gray-200">
						<button
							type="button"
							class="flex items-center justify-between w-full text-left text-sm font-semibold text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
							@click="toggleSection('attachments')"
							:aria-expanded="sectionStates.attachments"
							aria-controls="attachments-section"
						>
							<div class="flex items-center gap-2">
								<Paperclip class="w-4 h-4 text-blue-600" />
								<span>{{ translate("Attachments") }}</span>
								<span v-if="attachments.length > 0" class="text-xs text-gray-500">
									({{ attachments.length }})
								</span>
							</div>
							<ChevronDown
								class="w-3 h-3 text-gray-400 transition-transform"
								:class="sectionStates.attachments ? 'rotate-180' : ''"
							/>
						</button>
					</header>
					<Transition name="fade">
						<div
							id="attachments-section"
							v-show="sectionStates.attachments"
							class="px-4 pb-4 pt-3 space-y-3"
							@dragover="handleDragOver"
							@dragleave="handleDragLeave"
							@drop="handleDrop"
						>
							<!-- Upload controls -->
							<div class="flex items-center justify-between">
								<h3 class="text-sm font-medium text-gray-700">
									{{ translate("Attachments") }}
								</h3>
								<button
									type="button"
									@click="triggerFileInput"
									:disabled="isUploading"
									class="flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50"
								>
									<Upload class="w-3.5 h-3.5" />
									{{ translate("Add file") }}
								</button>
								<input
									ref="fileInputRef"
									type="file"
									accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv"
									multiple
									class="hidden"
									@change="handleFileSelect"
								/>
							</div>

							<!-- Upload progress -->
							<div v-if="isUploading" class="space-y-1">
								<div class="h-1.5 bg-gray-200 rounded-full overflow-hidden">
									<div
										class="h-full bg-blue-500 rounded-full transition-all"
										:style="{ width: uploadProgress + '%' }"
									/>
								</div>
								<p class="text-xs text-gray-500 text-center">
									{{ translate("Uploading") }}... {{ uploadProgress }}%
								</p>
							</div>

							<!-- Drag & Drop overlay -->
							<div
								v-if="isDragOver"
								class="border-2 border-dashed border-blue-400 bg-blue-50 rounded-lg p-6 text-center"
							>
								<Upload class="w-6 h-6 text-blue-400 mx-auto mb-1" />
								<p class="text-sm text-blue-600">{{ translate("Drop files here") }}</p>
							</div>

							<!-- Loading -->
							<div v-if="attachmentsLoading" class="text-center py-4">
								<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
							</div>

							<!-- Empty state -->
							<div
								v-else-if="attachments.length === 0 && !isDragOver"
								class="text-sm text-gray-500 text-center py-4"
							>
								{{ translate("No attachments") }}
							</div>

							<!-- Attachment grid -->
							<div v-else class="grid grid-cols-3 gap-2">
								<div
									v-for="file in attachments"
									:key="file.name"
									class="group relative rounded-lg border border-gray-200 overflow-hidden bg-gray-50 hover:border-blue-300 transition-colors cursor-pointer"
									@click="realWindow?.open(file.file_url, '_blank')"
								>
									<!-- Image thumbnail -->
									<div v-if="isImageFile(file)" class="aspect-square">
										<img
											:src="file.file_url"
											:alt="file.file_name"
											class="w-full h-full object-cover"
											loading="lazy"
										/>
									</div>
									<!-- Non-image file -->
									<div v-else class="aspect-square flex flex-col items-center justify-center p-2">
										<FileText class="w-8 h-8 text-gray-400 mb-1" />
										<span class="text-[10px] text-gray-500 truncate w-full text-center">
											{{ file.file_name }}
										</span>
									</div>
									<!-- File info overlay -->
									<div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
										<p class="text-[10px] text-white truncate">{{ file.file_name }}</p>
										<p v-if="file.file_size" class="text-[9px] text-white/70">{{ formatFileSize(file.file_size) }}</p>
									</div>
									<!-- Delete button -->
									<button
										@click.stop="deleteAttachment(file.name)"
										class="absolute top-1 right-1 p-1 rounded-full bg-white/80 hover:bg-red-100 text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
										:title="translate('Delete attachment')"
									>
										<Trash2 class="w-3 h-3" />
									</button>
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
											:title="translate('Delete time log')"
										>
											<Trash2 class="w-3.5 h-3.5" />
										</button>
									</div>
								</div>
							</div>
						</div>
					</Transition>
				</section>
			</div>
		</div>

		<!-- Footer -->
		<div class="border-t border-gray-200 px-4 py-3">
			<div class="flex items-center justify-between text-xs text-gray-500">
				<div class="flex items-center gap-3">
					<span v-if="task.creation">{{ translate('Created') }} {{ task.creation }}</span>
					<span
						v-if="autosaveIndicatorVisible"
						class="text-emerald-600 flex items-center gap-1 font-semibold"
					>
						<span aria-hidden="true">✓</span>
						{{ translate("Saved") }}
					</span>
				</div>
				<span v-if="isSaving" class="text-blue-600">{{ translate("Saving...") }}</span>
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
