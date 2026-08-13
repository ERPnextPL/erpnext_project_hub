<script setup>
import { computed } from "vue";
import { Calendar, User, Flag } from "lucide-vue-next";
import { translate } from "../utils/translation";
import { TASK_STATUSES, getStatusBadge } from "../utils/taskStatus";

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

defineEmits(["click"]);

const statusConfig = Object.fromEntries(
	TASK_STATUSES.map((status) => [status, getStatusBadge(status)])
);

const priorityClassMap = {
	Urgent: "text-red-600",
	High: "text-orange-500",
	Medium: "text-yellow-500",
	Low: "text-gray-400",
};

const priorityLabelMap = {
	Urgent: translate("Urgent"),
	High: translate("High"),
	Medium: translate("Medium"),
	Low: translate("Low"),
};

const statusInfo = computed(() => statusConfig[props.task.status] || getStatusBadge(props.task.status));

const indentStyle = computed(() => {
	return {
		marginLeft: `${Math.min(props.level * 12, 36)}px`,
	};
});

const assigneeLabel = computed(() => {
	if (!props.task._assign) return null;
	try {
		const assigned = JSON.parse(props.task._assign);
		if (!Array.isArray(assigned) || assigned.length === 0) return null;
		return assigned[0].split("@")[0].replace(/[._]/g, " ");
	} catch {
		return null;
	}
});

const formattedDate = computed(() => {
	if (!props.task.exp_end_date) return translate("No deadline");
	return props.task.exp_end_date;
});
</script>

<template>
	<button
		type="button"
		class="block w-full rounded-xl border border-gray-200 bg-white p-3 text-left shadow-sm transition-colors active:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:active:bg-gray-700"
		:style="indentStyle"
		@click="$emit('click', task)"
	>
		<div class="flex items-start justify-between gap-3">
			<div class="min-w-0 flex-1">
				<div class="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
					{{ task.subject }}
				</div>
				<div v-if="task.description" class="mt-1 line-clamp-2 text-xs text-gray-500 dark:text-gray-400">
					{{ task.description }}
				</div>
			</div>
			<span
				:class="[
					'inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium',
					statusInfo.class,
				]"
			>
				<component :is="statusInfo.icon" class="h-3 w-3" />
				{{ statusInfo.label || translate(task.status) }}
			</span>
		</div>

		<div class="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-gray-500 dark:text-gray-400">
			<span class="inline-flex items-center gap-1">
				<Calendar class="h-3.5 w-3.5" />
				{{ formattedDate }}
			</span>
			<span v-if="assigneeLabel" class="inline-flex items-center gap-1">
				<User class="h-3.5 w-3.5" />
				{{ assigneeLabel }}
			</span>
			<span
				v-if="task.priority"
				:class="['inline-flex items-center gap-1 font-medium', priorityClassMap[task.priority] || 'text-gray-400']"
			>
				<Flag class="h-3.5 w-3.5" />
				{{ priorityLabelMap[task.priority] || translate(task.priority) }}
			</span>
		</div>
	</button>
</template>
