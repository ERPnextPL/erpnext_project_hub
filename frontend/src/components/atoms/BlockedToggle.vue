<script setup>
import { computed } from "vue";
import { Lock } from "lucide-vue-next";
import { translate } from "../../utils/translation";

// Lock button that shows and switches a task's "is_blocked" flag.
// Always visible while the task is blocked; otherwise only on row hover.
const props = defineProps({
	blocked: {
		type: [Boolean, Number],
		default: false,
	},
	disabled: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["toggle"]);

const isBlocked = computed(() => Boolean(props.blocked));
const title = computed(() =>
	isBlocked.value ? translate("Blocked - click to unblock") : translate("Mark as blocked")
);
</script>

<template>
	<button
		type="button"
		:disabled="disabled"
		:title="title"
		:aria-label="title"
		:aria-pressed="isBlocked"
		@click.stop="emit('toggle', !isBlocked)"
		:class="[
			'inline-flex items-center justify-center w-6 h-6 rounded-full flex-shrink-0 transition-colors',
			isBlocked
				? 'bg-red-100 text-red-600 border border-red-200 hover:bg-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-800'
				: 'opacity-0 group-hover:opacity-100 focus:opacity-100 text-gray-400 hover:text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700',
		]"
	>
		<Lock class="w-3.5 h-3.5" />
	</button>
</template>
