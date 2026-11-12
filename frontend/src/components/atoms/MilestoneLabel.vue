<script setup>
import { computed } from "vue";
import { Diamond } from "lucide-vue-next";

// Coloured label of the milestone a task belongs to (like a Trello card label).
const props = defineProps({
	label: {
		type: String,
		required: true,
	},
	color: {
		type: String,
		default: "#3b82f6",
	},
});

const style = computed(() => ({ backgroundColor: props.color || "#3b82f6" }));
</script>

<template>
	<span
		class="inline-flex max-w-full items-center gap-1 rounded px-2 py-0.5 text-[11px] font-semibold text-white shadow-sm"
		:style="style"
		:title="label"
	>
		<Diamond class="h-3 w-3 flex-shrink-0" />
		<span class="truncate">{{ label }}</span>
	</span>
</template>
