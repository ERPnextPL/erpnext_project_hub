<script setup>
import { ref, computed } from "vue";
import { useTaskStore } from "../stores/taskStore";
import { getRealWindow, translate } from "../utils/translation";
import dayjs from "dayjs";
import {
	Circle,
	Clock,
	CheckCircle2,
	AlertCircle,
	Flag,
	Calendar,
	ChevronRight,
	ChevronDown,
	User,
	Diamond,
	Plus,
	FileText,
} from "lucide-vue-next";

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
	level: {
		type: Number,
		default: 0,
	},
});

const emit = defineEmits(["click", "update", "add-subtask"]);

const store = useTaskStore();
const isUpdating = ref(false);
const realWindow = getRealWindow();

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

const currentStatus = computed(() => statusConfig[props.task.status] || statusConfig["Open"]);
const currentPriority = computed(() => priorityConfig[props.task.priority] || priorityConfig["Medium"]);

const hasChildren = computed(() => store.tasks.some((t) => t.parent_task === props.task.name));
const isExpanded = computed(() => store.expandedTasks.has(props.task.name));

const canAddSubtask = computed(() => {
	return !["Completed", "Cancelled"].includes(props.task.status);
});

const assignedUsers = computed(() => {
	if (!props.task._assign) return [];
	try {
		const assigns = JSON.parse(props.task._assign);
		return Array.isArray(assigns) ? assigns : [];
	} catch {
		return [];
	}
});

const firstAssignee = computed(() => {
	if (assignedUsers.value.length === 0) return null;
	const email = assignedUsers.value[0];
	const name = email.split("@")[0];
	return {
		email,
		displayName: name.charAt(0).toUpperCase() + name.slice(1).replace(/[._]/g, " "),
		initials: name.charAt(0).toUpperCase(),
	};
});

const milestoneLabel = computed(() => {
	if (!props.task.milestone) return "";
	const milestone = store.milestones.find((m) => m.name === props.task.milestone);
	return milestone?.milestone_name || props.task.milestone;
});

const milestoneColor = computed(() => {
	if (!props.task.milestone) return null;
	const milestone = store.milestones.find((m) => m.name === props.task.milestone);
	return milestone?.color || "#3b82f6";
});

const formattedDate = computed(() => {
	if (!props.task.exp_end_date) return null;
	return dayjs(props.task.exp_end_date).format("DD MMM");
});

const isOverdue = computed(() => {
	if (!props.task.exp_end_date) return false;
	if (props.task.status === "Completed" || props.task.status === "Cancelled") return false;
	return dayjs(props.task.exp_end_date).isBefore(dayjs(), "day");
});

const dateClass = computed(() => {
	if (isOverdue.value) return "text-red-600 font-medium";
	if (!props.task.exp_end_date) return "text-gray-400";
	const today = dayjs().startOf("day");
	const dueDate = dayjs(props.task.exp_end_date).startOf("day");
	const diff = dueDate.diff(today, "day");
	if (diff === 0) return "text-amber-600 font-medium";
	if (diff <= 3) return "text-amber-500";
	return "text-gray-500";
});

async function toggleComplete(e) {
	e.stopPropagation();
	const newStatus = props.task.status === "Completed" ? "Open" : "Completed";
	isUpdating.value = true;
	try {
		emit("update", props.task.name, { status: newStatus });
	} finally {
		isUpdating.value = false;
	}
}

function handleClick() {
	emit("click", props.task);
}

function toggleExpand(e) {
	e.stopPropagation();
	store.toggleExpand(props.task.name);
}

function handleAddSubtask(e) {
	e.stopPropagation();
	emit("add-subtask", props.task.name);
}
</script>

<template>
	<div
		@click="handleClick"
		:class="[
			'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 active:bg-gray-50 dark:active:bg-gray-700 transition-colors',
			isOverdue && 'border-l-4 border-l-red-500',
			isUpdating && 'opacity-60',
			level > 0 && 'ml-4 border-l-2 border-l-blue-200 dark:border-l-blue-500/40',
		]"
	>
		<div class="flex items-start gap-2.5">
			<!-- Checkbox -->
			<button
				@click="toggleComplete"
				class="flex-shrink-0 mt-0.5 p-0.5"
				:disabled="isUpdating"
			>
				<CheckCircle2
					:class="[
						'w-5 h-5 transition-colors',
						task.status === 'Completed' ? 'text-green-600' : 'text-gray-300',
					]"
				/>
			</button>

			<!-- Content -->
			<div class="flex-1 min-w-0">
				<!-- Subject -->
				<h3
					:class="[
						'text-sm font-medium text-gray-900 dark:text-gray-100 mb-1',
						task.status === 'Completed' && 'line-through text-gray-400 dark:text-gray-500',
					]"
				>
					{{ task.subject }}
				</h3>

				<!-- Meta row -->
				<div class="flex flex-wrap items-center gap-1.5 text-xs">
					<!-- Status badge -->
					<span
						:class="[
							'inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full font-medium',
							currentStatus.bg,
							currentStatus.class,
						]"
					>
						<component :is="currentStatus.icon" class="w-3 h-3" />
						{{ currentStatus.label }}
					</span>

					<!-- Priority -->
					<span
						v-if="task.priority"
						:class="[
							'inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full',
							currentPriority.bg,
							currentPriority.class,
						]"
					>
						<Flag class="w-3 h-3" />
						{{ currentPriority.label }}
					</span>

					<!-- Due date -->
					<span
						v-if="task.exp_end_date"
						:class="['inline-flex items-center gap-1', dateClass]"
					>
						<Calendar class="w-3 h-3" />
						{{ formattedDate }}
						<span
							v-if="isOverdue"
							class="px-1 bg-red-100 text-red-700 rounded font-medium"
						>
							{{ translate("Overdue") }}
						</span>
					</span>
				</div>

				<!-- Second meta row: assignee, milestone, children -->
				<div class="flex flex-wrap items-center gap-2 mt-1.5 text-xs">
					<!-- Assignee -->
					<div
						v-if="firstAssignee"
						class="flex items-center gap-1 text-gray-500 dark:text-gray-400"
					>
						<div
							class="w-4 h-4 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-[10px] font-medium text-blue-700 dark:text-blue-300"
						>
							{{ firstAssignee.initials }}
						</div>
						<span class="truncate max-w-[80px]">{{ firstAssignee.displayName }}</span>
						<span v-if="assignedUsers.length > 1" class="text-gray-400">
							+{{ assignedUsers.length - 1 }}
						</span>
					</div>

					<!-- Milestone -->
					<span
						v-if="task.milestone"
						class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[11px] font-medium"
						:style="{
							color: milestoneColor || '#3b82f6',
							borderColor: milestoneColor || '#93c5fd',
						}"
					>
						<Diamond class="w-3 h-3 flex-shrink-0" />
						<span class="truncate max-w-[100px]">{{ milestoneLabel }}</span>
					</span>

					<!-- Expand children -->
					<button
						v-if="hasChildren"
						@click="toggleExpand"
						class="inline-flex items-center gap-0.5 text-gray-500 dark:text-gray-400 hover:text-gray-700"
					>
						<component :is="isExpanded ? ChevronDown : ChevronRight" class="w-3.5 h-3.5" />
						<span>{{ translate("Subtasks") }}</span>
					</button>

					<!-- Add subtask -->
					<button
						v-if="canAddSubtask"
						@click="handleAddSubtask"
						class="inline-flex items-center gap-0.5 text-gray-400 hover:text-blue-600"
					>
						<Plus class="w-3 h-3" />
					</button>
				</div>
			</div>

			<!-- Arrow -->
			<ChevronRight class="w-4 h-4 text-gray-400 flex-shrink-0 mt-1" />
		</div>
	</div>
</template>
