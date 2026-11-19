<script setup>
import { computed } from "vue";
import { getProgressColorClass } from "../../utils/progressColors";

// Thin progress bar (0-100) using the shared progress colour scale.
const props = defineProps({
	value: {
		type: [Number, String],
		default: 0,
	},
	height: {
		type: String,
		default: "h-1",
	},
});

const percent = computed(() => {
	const raw = Number(props.value ?? 0);
	return Number.isFinite(raw) ? Math.max(0, Math.min(100, raw)) : 0;
});
</script>

<template>
	<div
		:class="['w-full overflow-hidden rounded-full bg-gray-100', height]"
		role="progressbar"
		:aria-valuenow="percent"
		aria-valuemin="0"
		aria-valuemax="100"
	>
		<div
			:class="['h-full rounded-full transition-all duration-300', getProgressColorClass(percent)]"
			:style="{ width: percent + '%' }"
		></div>
	</div>
</template>
