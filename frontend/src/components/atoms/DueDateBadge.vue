<script setup>
import { computed } from "vue";
import { Calendar, CheckCircle2 } from "lucide-vue-next";
import { getDueState } from "../../utils/taskDueDate";
import { translate } from "../../utils/translation";

// Due date chip coloured by urgency: green when the task is done, red when
// overdue, amber for today and the next few days.
const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
	interactive: {
		type: Boolean,
		default: false,
	},
});

defineEmits(["click"]);

const state = computed(() => getDueState(props.task));

const TONE_CLASSES = {
	done: "bg-green-600 text-white",
	overdue: "bg-red-600 text-white",
	today: "bg-amber-500 text-white",
	soon: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
	normal: "text-gray-600 dark:text-gray-300",
};

const toneClass = computed(() => TONE_CLASSES[state.value.tone] || TONE_CLASSES.normal);

const title = computed(() => {
	if (state.value.tone === "overdue") return `${translate("Overdue")}: ${props.task.exp_end_date}`;
	return props.task.exp_end_date || "";
});
</script>

<template>
	<component
		:is="interactive ? 'button' : 'span'"
		v-if="state.tone !== 'none'"
		:type="interactive ? 'button' : undefined"
		:title="title"
		:class="[
			'inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium',
			toneClass,
			interactive && 'cursor-pointer hover:brightness-95',
		]"
		@click="interactive && $emit('click', $event)"
	>
		<component :is="state.tone === 'done' ? CheckCircle2 : Calendar" class="h-3 w-3" />
		<span>{{ state.label }}</span>
	</component>
</template>
