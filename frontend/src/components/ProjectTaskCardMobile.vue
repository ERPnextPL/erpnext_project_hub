<script setup>
import { computed } from "vue";
import { Calendar, Circle, Clock, AlertCircle, CheckCircle2, User, Flag } from "lucide-vue-next";
import { translate } from "../utils/translation";

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

const statusConfig = {
	Open: {
		icon: Circle,
		class: "bg-blue-100 text-blue-700 border-blue-200",
	},
	Working: {
		icon: Clock,
		class: "bg-amber-100 text-amber-700 border-amber-200",
	},
	"Pending Review": {
		icon: AlertCircle,
		class: "bg-purple-100 text-purple-700 border-purple-200",
	},
	Completed: {
		icon: CheckCircle2,
		class: "bg-green-100 text-green-700 border-green-200",
	},
	Overdue: {
		icon: AlertCircle,
		class: "bg-red-100 text-red-700 border-red-200",
	},
	Cancelled: {
		icon: Circle,
		class: "bg-gray-100 text-gray-600 border-gray-200",
	},
};

const priorityClassMap = {
	Urgent: "text-red-600",
	High: "text-orange-500",
	Medium: "text-yellow-500",
	Low: "text-gray-400",
};

const statusInfo = computed(() => {
	return (
		statusConfig[props.task.status] || {
			icon: Circle,
			class: "bg-gray-100 text-gray-600 border-gray-200",
		}
	);
});

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
				{{ task.status }}
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
				{{ task.priority }}
			</span>
		</div>
	</button>
</template>
