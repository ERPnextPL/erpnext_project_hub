<script setup>
import { computed } from "vue";
import { getStatusBadge } from "../../utils/taskStatus";

const props = defineProps({
	status: {
		type: String,
		required: true,
	},
	size: {
		type: String,
		default: "sm", // 'xs', 'sm', 'md'
	},
	showLabel: {
		type: Boolean,
		default: true,
	},
});

const config = computed(() => getStatusBadge(props.status));

const sizeClasses = computed(() => {
	switch (props.size) {
		case "xs":
			return {
				badge: "px-1.5 py-0.5 text-xs",
				icon: "w-3 h-3",
			};
		case "md":
			return {
				badge: "px-3 py-1.5 text-sm",
				icon: "w-4 h-4",
			};
		default: // sm
			return {
				badge: "px-2 py-1 text-xs",
				icon: "w-3.5 h-3.5",
			};
	}
});
</script>

<template>
	<span
		:class="[
			'inline-flex items-center gap-1 rounded-full font-medium border',
			config.class,
			sizeClasses.badge,
		]"
	>
		<component :is="config.icon" :class="sizeClasses.icon" />
		<span v-if="showLabel">{{ config.label }}</span>
	</span>
</template>
