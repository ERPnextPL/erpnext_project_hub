<script setup>
import { computed } from "vue";
import { Diamond } from "lucide-vue-next";
import { DEFAULT_MILESTONE_COLOR } from "../../utils/milestone";
import { translate } from "../../utils/translation";

// Coloured label of the milestone a task belongs to (like a Trello card label).
const props = defineProps({
	label: {
		type: String,
		required: true,
	},
	color: {
		type: String,
		default: DEFAULT_MILESTONE_COLOR,
	},
	size: {
		type: String,
		default: "sm", // 'xs' for list rows, 'sm' for cards
	},
});

const style = computed(() => ({ backgroundColor: props.color || DEFAULT_MILESTONE_COLOR }));
const sizeClass = computed(() =>
	props.size === "xs" ? "px-1.5 py-px text-[10px]" : "px-2 py-0.5 text-[11px]"
);
</script>

<template>
	<span
		:class="[
			'inline-flex max-w-full items-center gap-1 rounded font-semibold text-white shadow-sm',
			sizeClass,
		]"
		:style="style"
		:title="`${translate('Milestone')}: ${label}`"
	>
		<Diamond class="h-3 w-3 flex-shrink-0" />
		<span class="truncate">{{ label }}</span>
	</span>
</template>
