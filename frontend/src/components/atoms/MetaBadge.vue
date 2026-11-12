<script setup>
// Small icon + text badge for card metadata (subtasks, hours, description...).
defineProps({
	icon: {
		type: [Object, Function],
		required: true,
	},
	text: {
		type: [String, Number],
		default: "",
	},
	title: {
		type: String,
		default: "",
	},
	tone: {
		type: String,
		default: "text-gray-500 dark:text-gray-400",
	},
});
</script>

<template>
	<span :class="['inline-flex items-center gap-1 text-xs', tone]" :title="title">
		<component :is="icon" class="h-3.5 w-3.5" />
		<span v-if="text !== '' && text !== null">{{ text }}</span>
	</span>
</template>
