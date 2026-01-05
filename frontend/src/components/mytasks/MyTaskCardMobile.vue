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
	Folder,
	CornerDownRight,
	Plus,
	ChevronRight,
	FileText,
} from "lucide-vue-next";

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
});

const store = useMyTasksStore();
const isUpdating = ref(false);
const showSubtaskForm = ref(false);
const subtaskSubject = ref("");
const realWindow = getRealWindow();

// Status config
const statusConfig = {
	Open: { icon: Circle, class: "text-blue-600", bg: "bg-blue-100", label: translate("Open") },
	Working: {
		icon: Clock,
		class: "text-amber-600",
		bg: "bg-amber-100",
		label: translate("Working"),
	},
	"Pending Review": {
		icon: AlertCircle,
		class: "text-purple-600",
		bg: "bg-purple-100",
		label: translate("Pending Review"),
	},
	Completed: {
		icon: CheckCircle2,
		class: "text-green-600",
		bg: "bg-green-100",
		label: translate("Completed"),
	},
	Overdue: {
		icon: AlertCircle,
		class: "text-red-600",
		bg: "bg-red-100",
		label: translate("Overdue"),
	},
	Cancelled: {
		icon: Circle,
		class: "text-gray-400",
		bg: "bg-gray-100",
		label: translate("Cancelled"),
	},
};

const priorityConfig = {
	Urgent: { class: "text-red-600", label: translate("Urgent") },
	High: { class: "text-orange-500", label: translate("High") },
	Medium: { class: "text-yellow-600", label: translate("Medium") },
	Low: { class: "text-gray-500", label: translate("Low") },
};

const currentStatus = computed(() => {
	return statusConfig[props.task.status] || statusConfig["Open"];
});

const currentPriority = computed(() => {
	return priorityConfig[props.task.priority] || priorityConfig["Medium"];
});

const taskDescription = computed(() => (props.task.description || "").trim());
const descriptionPreviewLabel = computed(() => {
	if (!taskDescription.value) {
		return "";
	}
	const firstLine = taskDescription.value.split("\n")[0]?.trim();
	return firstLine || "";
});
const showDescriptionPreview = ref(false);

const formattedDate = computed(() => {
	if (!props.task.exp_end_date) return null;
	return dayjs(props.task.exp_end_date).format("DD MMM YYYY");
});

const canAddSubtask = computed(() => {
	return !["Completed", "Cancelled"].includes(props.task.status);
});

const dateClass = computed(() => {
	if (props.task.is_overdue) return "text-red-600 font-medium";
	if (!props.task.exp_end_date) return "text-gray-400";

	const today = dayjs().startOf("day");
	const dueDate = dayjs(props.task.exp_end_date).startOf("day");
	const diff = dueDate.diff(today, "day");

	if (diff === 0) return "text-amber-600 font-medium";
	if (diff <= 3) return "text-amber-500";
	return "text-gray-500";
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

async function toggleComplete(e) {
	e.stopPropagation();
	const newStatus = props.task.status === "Completed" ? "Open" : "Completed";

	isUpdating.value = true;
	try {
		await store.quickUpdateTask(props.task.name, { status: newStatus });
	} finally {
		isUpdating.value = false;
	}
}

function openTask() {
	showDescriptionPreview.value = false;
	store.selectTask(props.task);
}

async function createSubtask() {
	const subject = subtaskSubject.value.trim();
	if (!subject) return;
	try {
		await store.createTask({
			subject,
			project: props.task.project,
			parent_task: props.task.name,
		});
		subtaskSubject.value = "";
		showSubtaskForm.value = false;
	} catch (e) {
		// handled by store/api
	}
}

function toggleDescriptionPreview(event) {
	event.stopPropagation();
	if (!taskDescription.value) return;
	showDescriptionPreview.value = !showDescriptionPreview.value;
}

function handleDocumentClick(event) {
	if (
		showDescriptionPreview.value &&
		!event.target.closest(".description-preview-trigger-mobile")
	) {
		showDescriptionPreview.value = false;
	}
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
		:class="[
			'bg-white rounded-lg border border-gray-200 p-4 active:bg-gray-50 transition-colors',
			task.is_overdue && 'border-l-4 border-l-red-500',
			isUpdating && 'opacity-60',
		]"
	>
		<div class="flex items-start gap-3">
			<!-- Checkbox -->
			<button
				@click="toggleComplete"
				class="flex-shrink-0 mt-0.5 p-0.5"
				:disabled="isUpdating"
			>
				<CheckCircle2
					:class="[
						'w-6 h-6 transition-colors',
						task.status === 'Completed' ? 'text-green-600' : 'text-gray-300',
					]"
				/>
			</button>

			<!-- Content -->
			<div class="flex-1 min-w-0">
				<!-- Subject -->
				<h3
					:class="[
						'font-medium text-gray-900 mb-1',
						task.status === 'Completed' && 'line-through text-gray-400',
					]"
				>
					{{ task.subject }}
				</h3>

				<div
					v-if="taskDescription"
					class="relative text-xs text-gray-500 description-preview-trigger-mobile"
				>
					<button
						type="button"
						class="flex items-center gap-1 hover:text-gray-700 focus:outline-none"
						@click.stop="toggleDescriptionPreview"
						:title="translate('Hover to preview description')"
					>
						<FileText class="w-3.5 h-3.5" />
						<span v-if="descriptionPreviewLabel">{{ descriptionPreviewLabel }}</span>
					</button>

					<Transition name="fade">
						<div
							v-if="showDescriptionPreview"
							class="absolute left-0 top-full z-40 mt-2 w-full rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-700 shadow-lg whitespace-pre-line break-words"
						>
							{{ taskDescription }}
						</div>
					</Transition>
				</div>

				<div
					v-if="task.parent_task"
					class="flex items-center gap-1 text-xs text-gray-500 mb-2"
					:title="task.parent_subject || task.parent_task"
				>
					<CornerDownRight class="w-3.5 h-3.5 flex-shrink-0" />
					<span class="truncate"
						>{{ translate("Subtask") }}:
						{{ task.parent_subject || task.parent_task }}</span
					>
				</div>

				<div v-if="canAddSubtask" class="mb-2">
					<button
						@click.stop="showSubtaskForm = !showSubtaskForm"
						class="text-xs text-gray-500 hover:text-gray-700 hover:underline inline-flex items-center gap-1"
					>
						<Plus class="w-3.5 h-3.5" />
						{{ translate("Add subtask") }}
					</button>
				</div>

				<div v-if="showSubtaskForm" class="mb-3 flex items-center gap-2" @click.stop>
					<input
						v-model="subtaskSubject"
						type="text"
						class="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
						:placeholder="translate('Subtask name...')"
						@keydown.enter.prevent="createSubtask"
					/>
					<button
						@click="createSubtask"
						class="px-2.5 py-1 text-xs font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
					>
						{{ translate("Add") }}
					</button>
				</div>

				<!-- Meta row -->
				<div class="flex flex-wrap items-center gap-2 text-sm">
					<!-- Project -->
					<div v-if="task.project_name" class="flex items-center gap-1 text-gray-500">
						<Folder class="w-3.5 h-3.5" />
						<span class="truncate max-w-[120px]">{{ task.project_name }}</span>
					</div>

					<!-- Status badge -->
					<span
						:class="[
							'flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
							currentStatus.bg,
							currentStatus.class,
						]"
					>
						<component :is="currentStatus.icon" class="w-3 h-3" />
						{{ currentStatus.label }}
					</span>

					<!-- Priority -->
					<span :class="['flex items-center gap-1 text-xs', currentPriority.class]">
						<Flag class="w-3 h-3" />
						{{ currentPriority.label }}
					</span>
				</div>

				<!-- Due date -->
					<div
						v-if="task.exp_end_date || task.is_overdue"
						:class="['flex items-center gap-1 mt-2 text-sm', dateClass]"
					>
						<Calendar class="w-3.5 h-3.5" />
						<span>{{ formattedDate || translate("No deadline") }}</span>
						<span
							v-if="task.is_overdue"
							class="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded font-medium"
						>
							{{ translate("Overdue") }}
						</span>
					</div>

					<div
						v-if="task.progress !== null && task.progress !== undefined"
						class="mt-3 space-y-1"
					>
						<div class="flex items-center justify-between text-[11px] text-gray-500">
							<span>{{ translate("Progress") }}</span>
							<span class="font-semibold text-gray-700">{{ progressPercent }}%</span>
						</div>
						<div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
							<div
								class="h-full rounded-full transition-all duration-300"
								:class="progressBarColor"
								:style="{ width: progressPercent + '%' }"
							></div>
						</div>
					</div>
				</div>

			<!-- Arrow -->
			<ChevronRight class="w-5 h-5 text-gray-400 flex-shrink-0" />
		</div>
	</div>
</template>
