<script setup>
import { computed } from "vue";
import {
	Calendar,
	Clock,
	CornerDownRight,
	FileText,
	Folder,
	ListTodo,
	Lock,
	Pencil,
} from "lucide-vue-next";
import AssigneeAvatars from "../atoms/AssigneeAvatars.vue";
import DueDateBadge from "../atoms/DueDateBadge.vue";
import MetaBadge from "../atoms/MetaBadge.vue";
import MilestoneLabel from "../atoms/MilestoneLabel.vue";
import PriorityBadge from "../atoms/PriorityBadge.vue";
import ProgressBar from "../atoms/ProgressBar.vue";
import DatePickerPopover from "../DatePickerPopover.vue";
import { translate } from "../../utils/translation";

/**
 * Trello-like task card. Pure presentation: it knows nothing about stores, so
 * the project board and My Tasks render the very same card.
 */
const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
	users: {
		type: Array,
		default: () => [],
	},
	// { label, color } of the task's milestone, when the view knows milestones.
	milestone: {
		type: Object,
		default: null,
	},
	parentSubject: {
		type: String,
		default: "",
	},
	showProject: {
		type: Boolean,
		default: false,
	},
	// { total, done } of direct subtasks.
	subtaskStats: {
		type: Object,
		default: null,
	},
	menuOpen: {
		type: Boolean,
		default: false,
	},
	editable: {
		type: Boolean,
		default: true,
	},
});

const emit = defineEmits(["open", "menu", "update"]);

const isClosed = computed(() => ["Completed", "Cancelled"].includes(props.task.status));
const hasDescription = computed(() => Boolean((props.task.description || "").trim()));
const progress = computed(() => Number(props.task.progress) || 0);
const hasExpectedTime = computed(() => Number(props.task.expected_time) > 0);
const showPriority = computed(() => ["High", "Urgent"].includes(props.task.priority));

const subtaskText = computed(() => {
	const stats = props.subtaskStats;
	if (!stats?.total) return "";
	return stats.done ? `${stats.done}/${stats.total}` : String(stats.total);
});

const subtaskTone = computed(() =>
	props.subtaskStats?.total && props.subtaskStats.done === props.subtaskStats.total
		? "text-green-600 dark:text-green-400"
		: "text-gray-500 dark:text-gray-400"
);

function setDueDate(value) {
	if ((value || "") !== (props.task.exp_end_date || "")) {
		emit("update", { exp_end_date: value || null });
	}
}

function onContextMenu(event) {
	event.preventDefault();
	emit("menu", event);
}
</script>

<template>
	<article
		role="button"
		tabindex="0"
		:aria-label="task.subject"
		:class="[
			'task-card group relative cursor-pointer rounded-lg border bg-white p-2.5 text-left shadow-sm transition-all',
			'hover:border-gray-300 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
			'dark:bg-gray-800 dark:hover:border-gray-500',
			task.is_blocked
				? 'border-red-200 dark:border-red-800'
				: 'border-gray-200 dark:border-gray-700',
			menuOpen && 'ring-2 ring-blue-400',
		]"
		@click="emit('open', task)"
		@keydown.enter.self="emit('open', task)"
		@contextmenu="onContextMenu"
	>
		<!-- Quick edit (Trello's pencil) -->
		<button
			type="button"
			class="absolute right-1.5 top-1.5 z-10 rounded-md bg-white/90 p-1 text-gray-500 opacity-0 shadow-sm transition-opacity hover:bg-gray-100 hover:text-gray-800 focus:opacity-100 group-hover:opacity-100 dark:bg-gray-700/90 dark:text-gray-300 dark:hover:bg-gray-600"
			:class="menuOpen && 'opacity-100'"
			:title="translate('Quick actions')"
			:aria-label="translate('Quick actions')"
			@click.stop="emit('menu', $event)"
		>
			<Pencil class="h-3.5 w-3.5" />
		</button>

		<!-- Labels -->
		<div v-if="milestone || showPriority" class="mb-1.5 flex flex-wrap items-center gap-1 pr-6">
			<MilestoneLabel v-if="milestone" :label="milestone.label" :color="milestone.color" />
			<PriorityBadge v-if="showPriority" :priority="task.priority" size="xs" />
		</div>

		<!-- Parent task -->
		<div
			v-if="parentSubject"
			class="mb-0.5 flex items-center gap-1 pr-6 text-[11px] text-gray-500 dark:text-gray-400"
			:title="parentSubject"
		>
			<CornerDownRight class="h-3 w-3 flex-shrink-0" />
			<span class="truncate">{{ parentSubject }}</span>
		</div>

		<!-- Title -->
		<p
			:class="[
				'task-card-title break-words pr-6 text-sm leading-snug',
				isClosed
					? 'text-gray-500 line-through dark:text-gray-400'
					: 'text-gray-900 dark:text-gray-100',
			]"
		>
			{{ task.subject }}
		</p>

		<!-- Project (cross-project views) -->
		<div
			v-if="showProject && (task.project_name || task.project)"
			class="mt-1 flex items-center gap-1 text-[11px] text-gray-500 dark:text-gray-400"
		>
			<Folder class="h-3 w-3 flex-shrink-0" />
			<span class="truncate">{{ task.project_name || task.project }}</span>
		</div>

		<!-- Badges -->
		<div class="mt-2 flex flex-wrap items-center gap-x-2.5 gap-y-1.5" @click.stop>
			<span
				v-if="task.is_blocked"
				class="inline-flex items-center gap-1 rounded bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/40 dark:text-red-300"
			>
				<Lock class="h-3 w-3" />
				{{ translate("Blocked") }}
			</span>

			<DatePickerPopover
				v-if="editable"
				:id="`board-card-${task.name}`"
				:model-value="task.exp_end_date || ''"
				@update:model-value="setDueDate"
			>
				<template #trigger="{ open }">
					<DueDateBadge v-if="task.exp_end_date" :task="task" interactive @click="open" />
					<button
						v-else
						type="button"
						class="rounded p-0.5 text-gray-400 opacity-0 transition-opacity hover:bg-gray-100 hover:text-gray-600 focus:opacity-100 group-hover:opacity-100 dark:hover:bg-gray-700"
						:title="translate('Set due date')"
						:aria-label="translate('Set due date')"
						@click="open"
					>
						<Calendar class="h-3.5 w-3.5" />
					</button>
				</template>
			</DatePickerPopover>
			<DueDateBadge v-else :task="task" />

			<MetaBadge
				v-if="hasDescription"
				:icon="FileText"
				:title="translate('This task has a description')"
			/>
			<MetaBadge
				v-if="subtaskText"
				:icon="ListTodo"
				:text="subtaskText"
				:tone="subtaskTone"
				:title="translate('Subtasks')"
			/>
			<MetaBadge
				v-if="hasExpectedTime"
				:icon="Clock"
				:text="`${task.expected_time}h`"
				:title="translate('Expected time')"
			/>

			<AssigneeAvatars
				class="ml-auto"
				:assign="task._assign"
				:users="users"
				size="sm"
			/>
		</div>

		<ProgressBar v-if="progress > 0 && !isClosed" :value="progress" class="mt-2" />
	</article>
</template>
