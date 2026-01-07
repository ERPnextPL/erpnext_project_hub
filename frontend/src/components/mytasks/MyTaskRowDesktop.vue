<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useMyTasksStore } from "../../stores/myTasksStore";
import dayjs from "dayjs";
import { getRealWindow, translate } from "../../utils/translation";
import {
	Circle,
	Clock,
	CheckCircle2,
	AlertCircle,
	Flag,
	Calendar,
	ChevronDown,
	ChevronRight,
	Folder,
	CornerDownRight,
	FileText,
} from "lucide-vue-next";

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
	indentLevel: {
		type: Number,
		default: 0,
	},
	hierarchyEnabled: {
		type: Boolean,
		default: false,
	},
	hasChildren: {
		type: Boolean,
		default: false,
	},
	isExpanded: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["open-time-log-modal", "toggle-expand"]);

const store = useMyTasksStore();
const realWindow = getRealWindow();

const isUpdating = ref(false);

const isStatusDropdownOpen = computed(() => {
	return (
		store.inlineDropdown?.taskName === props.task.name &&
		store.inlineDropdown?.type === "status"
	);
});

const isPriorityDropdownOpen = computed(() => {
	return (
		store.inlineDropdown?.taskName === props.task.name &&
		store.inlineDropdown?.type === "priority"
	);
});

const showContextMenu = ref(false);
const contextMenuPosition = ref({ x: 0, y: 0 });

const canAddSubtask = computed(() => {
	return props.task.status !== "Completed" && props.task.status !== "Cancelled";
});

function isTouchDevice() {
	return Boolean(realWindow?.matchMedia?.("(hover: none)").matches);
}

// Status config - shorter labels to fit in grid
const statusConfig = {
	Open: {
		icon: Circle,
		class: "text-slate-700",
		bg: "bg-blue-100 border border-blue-200",
		label: translate("Open"),
	},
	Working: {
		icon: Clock,
		class: "text-white",
		bg: "bg-blue-600 border border-blue-600",
		label: translate("Working"),
	},
	"Pending Review": {
		icon: AlertCircle,
		class: "text-white",
		bg: "bg-purple-600 border border-purple-600",
		label: translate("Pending Review"),
	},
	Completed: {
		icon: CheckCircle2,
		class: "text-white",
		bg: "bg-emerald-600 border border-emerald-600",
		label: translate("Completed"),
	},
	Overdue: {
		icon: AlertCircle,
		class: "text-white",
		bg: "bg-red-600 border border-red-600",
		label: translate("Overdue"),
	},
	Cancelled: {
		icon: Circle,
		class: "text-slate-500",
		bg: "bg-gray-100 border border-gray-200",
		label: translate("Cancelled"),
	},
};

const priorityConfig = {
	Urgent: {
		class: "text-red-600",
		bg: "bg-red-100 border border-red-200",
		label: translate("Urgent"),
	},
	High: {
		class: "text-orange-600",
		bg: "bg-orange-100 border border-orange-200",
		label: translate("High"),
	},
	Medium: {
		class: "text-amber-600",
		bg: "bg-amber-100 border border-amber-200",
		label: translate("Medium"),
	},
	Low: {
		class: "text-slate-600",
		bg: "bg-slate-100 border border-slate-200",
		label: translate("Low"),
	},
};

const currentStatus = computed(() => {
	return statusConfig[props.task.status] || statusConfig["Open"];
});

const currentPriority = computed(() => {
	return priorityConfig[props.task.priority] || priorityConfig["Medium"];
});

const progressPercent = computed(() => {
	const raw = Number(props.task.progress ?? 0);
	if (Number.isNaN(raw)) return 0;
	return Math.max(0, Math.min(100, raw));
});

const progressBarColor = computed(() => {
	const percent = progressPercent.value;
	if (percent >= 90) return "bg-emerald-500";
	if (percent > 50) return "bg-amber-500";
	return "bg-blue-500";
});

const progressBarColorValue = computed(() => {
	const percent = progressPercent.value;
	if (percent >= 90) return "#10b981";
	if (percent > 50) return "#f59e0b";
	return "#3b82f6";
});

const taskDescription = computed(() => (props.task.description || "").trim());
const descriptionPreviewLabel = computed(() => {
	if (!taskDescription.value) {
		return "";
	}
	const firstLine = taskDescription.value.split("\n")[0]?.trim();
	return firstLine || "";
});

const formattedDate = computed(() => {
	if (!props.task.exp_end_date) return null;
	return dayjs(props.task.exp_end_date).format("DD MMM");
});

const dateClass = computed(() => {
	if (props.task.is_overdue) return "text-red-600 font-medium";
	if (!props.task.exp_end_date) return "text-gray-400";

	const today = dayjs().startOf("day");
	const dueDate = dayjs(props.task.exp_end_date).startOf("day");
	const diff = dueDate.diff(today, "day");

	if (diff === 0) return "text-amber-600 font-medium";
	if (diff <= 3) return "text-amber-500";
	return "text-gray-600";
});

async function updateStatus(newStatus) {
	store.closeInlineDropdown();
	if (newStatus === props.task.status) return;

	isUpdating.value = true;
	try {
		await store.quickUpdateTask(props.task.name, { status: newStatus });
	} finally {
		isUpdating.value = false;
	}
}

async function updatePriority(newPriority) {
	store.closeInlineDropdown();
	if (newPriority === props.task.priority) return;

	isUpdating.value = true;
	try {
		await store.quickUpdateTask(props.task.name, { priority: newPriority });
	} finally {
		isUpdating.value = false;
	}
}

function openTask() {
	store.selectTask(props.task);
}

function showMenu(e) {
	if (isTouchDevice()) return;
	e.preventDefault();
	e.stopPropagation();
	contextMenuPosition.value = { x: e.clientX, y: e.clientY };
	showContextMenu.value = true;

	const closeMenu = (evt) => {
		if (evt?.target?.closest?.(".mytasks-context-menu")) return;
		showContextMenu.value = false;
		document.removeEventListener("click", closeMenu);
	};
	setTimeout(() => document.addEventListener("click", closeMenu), 0);
}

function logTimeFromMenu() {
	emit("open-time-log-modal", props.task);
	showContextMenu.value = false;
}

function addSubtaskFromMenu() {
	if (!canAddSubtask.value) return;
	store.openNewSubtask(props.task);
	showContextMenu.value = false;
}

function handleDocumentClick(e) {
	if (e.target.closest(".status-dropdown") || e.target.closest(".priority-dropdown")) {
		return;
	}
	store.closeInlineDropdown();
}

onMounted(() => {
	document.addEventListener("click", handleDocumentClick);
});

onUnmounted(() => {
	document.removeEventListener("click", handleDocumentClick);
});
</script>

<template>
	<div
		@click="openTask"
		@contextmenu="showMenu"
		:style="props.indentLevel ? { paddingLeft: props.indentLevel * 16 + 'px' } : undefined"
		:class="[
			'grid grid-cols-12 gap-4 px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors items-center',
			isUpdating && 'opacity-60',
		]"
	>
		<!-- Task subject -->
		<div
			class="col-span-4 flex items-start gap-3 min-w-0"
			:title="taskDescription || undefined"
		>
			<button
				v-if="props.hierarchyEnabled && props.hasChildren"
				@click.stop="emit('toggle-expand', task.name)"
				class="flex-shrink-0 p-0.5 rounded hover:bg-gray-100 transition-colors mt-0.5"
				:title="
					props.isExpanded
						? translate('Collapse subtasks')
						: translate('Expand subtasks')
				"
			>
				<ChevronDown v-if="props.isExpanded" class="w-4 h-4 text-gray-500" />
				<ChevronRight v-else class="w-4 h-4 text-gray-500" />
			</button>
			<button
				@click.stop="updateStatus(task.status === 'Completed' ? 'Open' : 'Completed')"
				class="flex-shrink-0 p-0.5 rounded hover:bg-gray-100 transition-colors mt-0.5"
				:title="
					task.status === 'Completed'
						? translate('Mark as open')
						: translate('Mark as complete')
				"
			>
				<CheckCircle2
					:class="[
						'w-5 h-5 transition-colors',
						task.status === 'Completed'
							? 'text-green-600'
							: 'text-gray-300 hover:text-gray-400',
					]"
				/>
			</button>
			<div class="min-w-0">
				<div v-if="taskDescription" class="flex items-center gap-1 text-xs text-gray-400">
					<FileText class="w-3 h-3 flex-shrink-0" />
					<span v-if="descriptionPreviewLabel" class="truncate">{{
						descriptionPreviewLabel
					}}</span>
				</div>

				<div
					:class="[
						'font-medium text-sm text-gray-900 truncate',
						task.status === 'Completed' && 'line-through text-gray-400',
					]"
				>
					{{ task.subject }}
				</div>
				<div
					v-if="task.parent_task"
					class="mt-0.5 flex items-center gap-1 text-xs text-gray-500 truncate"
					:title="task.parent_subject || task.parent_task"
				>
					<CornerDownRight class="w-3.5 h-3.5 flex-shrink-0" />
					<span class="truncate"
						>{{ translate("Subtask") }}:
						{{ task.parent_subject || task.parent_task }}</span
					>
				</div>

				<div
					v-if="task.progress !== null && task.progress !== undefined"
					class="mt-2 space-y-1"
				>
					<div class="flex items-center justify-between text-xs text-gray-500">
						<span>{{ translate("Progress") }}</span>
						<span class="font-semibold text-gray-700">{{ progressPercent }}%</span>
					</div>
					<div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
						<div
							class="h-full rounded-full transition-all duration-300"
							:class="progressBarColor"
							:style="{ width: progressPercent + '%', backgroundColor: progressBarColorValue }"
						></div>
					</div>
				</div>
			</div>
		</div>

		<!-- Project -->
		<div class="col-span-2 flex items-center min-w-0">
			<div
				v-if="task.project_name"
				class="flex items-center gap-1.5 text-sm text-gray-500 truncate"
			>
				<Folder class="w-3.5 h-3.5 flex-shrink-0" />
				<span class="truncate">{{ task.project_name }}</span>
			</div>
			<span v-else class="text-gray-300">—</span>
		</div>

		<!-- Status -->
		<div class="col-span-2 flex items-center relative status-dropdown" @click.stop>
			<button
				@click="store.toggleInlineDropdown(task.name, 'status')"
				:class="[
					'flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium transition-colors',
					currentStatus.bg,
					currentStatus.class,
				]"
			>
				<component :is="currentStatus.icon" class="w-3.5 h-3.5" />
				{{ currentStatus.label }}
				<ChevronDown class="w-3 h-3" />
			</button>

			<!-- Status dropdown -->
			<Transition name="fade">
				<div
					v-if="isStatusDropdownOpen"
					class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20 min-w-[140px]"
				>
					<button
						v-for="(config, status) in statusConfig"
						:key="status"
						@click="updateStatus(status)"
						:class="[
							'w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left hover:bg-gray-50',
							task.status === status && 'bg-gray-50',
						]"
					>
						<component :is="config.icon" :class="['w-4 h-4', config.class]" />
						{{ config.label }}
					</button>
				</div>
			</Transition>
		</div>

		<!-- Priority -->
		<div class="col-span-2 flex items-center relative priority-dropdown" @click.stop>
					<button
						@click="store.toggleInlineDropdown(task.name, 'priority')"
						:class="[
							'flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors hover:bg-gray-100',
							currentPriority.bg,
							currentPriority.class,
						]"
						:title="currentPriority.label"
					>
				<Flag class="w-3.5 h-3.5" />
				<ChevronDown class="w-3 h-3" />
			</button>

			<!-- Priority dropdown -->
			<Transition name="fade">
				<div
					v-if="isPriorityDropdownOpen"
					class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20 min-w-[120px]"
				>
					<button
						v-for="(config, priority) in priorityConfig"
						:key="priority"
						@click="updatePriority(priority)"
						:class="[
							'w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left hover:bg-gray-50',
							task.priority === priority && 'bg-gray-50',
						]"
					>
						<Flag :class="['w-4 h-4', config.class]" />
						{{ config.label }}
					</button>
				</div>
			</Transition>
		</div>

		<!-- Due date -->
		<div class="col-span-2 flex items-center" @click.stop>
			<div :class="['flex items-center gap-1.5 text-sm', dateClass]">
				<Calendar class="w-3.5 h-3.5" />
				<span v-if="formattedDate">{{ formattedDate }}</span>
				<span v-else class="text-gray-300">{{ translate("No deadline") }}</span>
				<span
					v-if="task.is_overdue"
					class="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded"
				>
					!
				</span>
			</div>
		</div>

		<!-- Context menu -->
		<Teleport to="body">
			<div
				v-if="showContextMenu"
				class="mytasks-context-menu fixed bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50 min-w-[180px]"
				:style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }"
			>
				<button
					@click="logTimeFromMenu"
					class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
				>
					<Clock class="w-4 h-4" />
					{{ translate("Add time") }}
				</button>
				<button
					@click="addSubtaskFromMenu"
					:class="[
						'w-full px-3 py-2 text-left text-sm flex items-center gap-2',
						canAddSubtask
							? 'text-gray-700 hover:bg-gray-100'
							: 'text-gray-300 cursor-not-allowed',
					]"
					:disabled="!canAddSubtask"
				>
					<FileText class="w-4 h-4" />
					{{ translate("Add subtask") }}
				</button>
			</div>
		</Teleport>
	</div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
