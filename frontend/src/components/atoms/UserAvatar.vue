<script setup>
import { computed, ref, watch } from "vue";
import { getInitials } from "../../utils/taskAssignees";

// Round user avatar: photo when available, coloured initials otherwise.
const props = defineProps({
	name: {
		type: String,
		default: "",
	},
	fullName: {
		type: String,
		default: "",
	},
	image: {
		type: String,
		default: null,
	},
	size: {
		type: String,
		default: "sm", // 'xs', 'sm', 'md'
	},
	ring: {
		type: Boolean,
		default: false,
	},
});

const AVATAR_COLORS = [
	"bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-200",
	"bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-200",
	"bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-200",
	"bg-violet-100 text-violet-700 dark:bg-violet-900/50 dark:text-violet-200",
	"bg-pink-100 text-pink-700 dark:bg-pink-900/50 dark:text-pink-200",
	"bg-cyan-100 text-cyan-700 dark:bg-cyan-900/50 dark:text-cyan-200",
	"bg-orange-100 text-orange-700 dark:bg-orange-900/50 dark:text-orange-200",
	"bg-teal-100 text-teal-700 dark:bg-teal-900/50 dark:text-teal-200",
];

const imageFailed = ref(false);
watch(
	() => props.image,
	() => {
		imageFailed.value = false;
	}
);

const label = computed(() => props.fullName || props.name);
const initials = computed(() => getInitials(label.value));

const colorClass = computed(() => {
	let hash = 0;
	for (const char of String(props.name || label.value)) {
		hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
	}
	return AVATAR_COLORS[hash % AVATAR_COLORS.length];
});

const sizeClass = computed(
	() =>
		({
			xs: "h-5 w-5 text-[9px]",
			sm: "h-6 w-6 text-[10px]",
			md: "h-8 w-8 text-xs",
		}[props.size] || "h-6 w-6 text-[10px]")
);
</script>

<template>
	<span
		:title="label"
		:class="[
			'inline-flex flex-shrink-0 items-center justify-center overflow-hidden rounded-full font-semibold select-none',
			sizeClass,
			ring && 'ring-2 ring-white dark:ring-gray-800',
			image && !imageFailed ? 'bg-gray-100' : colorClass,
		]"
	>
		<img
			v-if="image && !imageFailed"
			:src="image"
			:alt="label"
			class="h-full w-full object-cover"
			@error="imageFailed = true"
		/>
		<template v-else>{{ initials }}</template>
	</span>
</template>
