<script setup>
import { computed } from "vue";
import { translate } from "../../utils/translation";
import { Circle, Clock, CheckCircle2, AlertCircle } from "lucide-vue-next";

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

// Status configuration - shared across all components
const statusConfig = {
	Open: {
		icon: Circle,
		class: "text-blue-600",
		bg: "bg-blue-100",
		border: "border-blue-200",
		label: translate("Open"),
	},
	Working: {
		icon: Clock,
		class: "text-amber-600",
		bg: "bg-amber-100",
		border: "border-amber-200",
		label: translate("Working"),
	},
	"Pending Review": {
		icon: AlertCircle,
		class: "text-purple-600",
		bg: "bg-purple-100",
		border: "border-purple-200",
		label: translate("Pending Review"),
	},
	Completed: {
		icon: CheckCircle2,
		class: "text-green-600",
		bg: "bg-green-100",
		border: "border-green-200",
		label: translate("Completed"),
	},
	Overdue: {
		icon: AlertCircle,
		class: "text-red-600",
		bg: "bg-red-100",
		border: "border-red-200",
		label: translate("Overdue"),
	},
	Cancelled: {
		icon: Circle,
		class: "text-gray-400",
		bg: "bg-gray-100",
		border: "border-gray-200",
		label: translate("Cancelled"),
	},
	Template: {
		icon: Circle,
		class: "text-gray-500",
		bg: "bg-gray-100",
		border: "border-gray-200",
		label: translate("Template"),
	},
};

const config = computed(() => {
	return statusConfig[props.status] || statusConfig["Open"];
});

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
			config.bg,
			config.class,
			config.border,
			sizeClasses.badge,
		]"
	>
		<component :is="config.icon" :class="sizeClasses.icon" />
		<span v-if="showLabel">{{ config.label }}</span>
	</span>
</template>
