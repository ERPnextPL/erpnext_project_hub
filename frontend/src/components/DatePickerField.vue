<script setup>
import { computed, ref } from "vue";
import { Calendar } from "lucide-vue-next";
import DatePickerPopover from "./DatePickerPopover.vue";
import { translate } from "../utils/translation";

const props = defineProps({
	id: { type: String, required: true },
	modelValue: { type: String, default: "" },
	disabled: Boolean,
	placeholder: { type: String, default: "Select date" },
	buttonClass: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue"]);
const buttonRef = ref(null);
defineExpose({ focus: () => buttonRef.value?.focus() });

const displayValue = computed(() => {
	if (!props.modelValue) return translate(props.placeholder);
	const [year, month, day] = props.modelValue.slice(0, 10).split("-").map(Number);
	return new Date(year, month - 1, day).toLocaleDateString(undefined, {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
	});
});
</script>

<template>
	<DatePickerPopover
		:id="id"
		:model-value="modelValue"
		:disabled="disabled"
		@update:model-value="emit('update:modelValue', $event)"
	>
		<template #trigger="{ open, isOpen }">
			<button
				ref="buttonRef"
				type="button"
				:disabled="disabled"
				:class="['flex h-10 w-full items-center gap-2 rounded-md border border-gray-300 bg-white px-3 text-left text-sm text-gray-700 transition-colors hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200', isOpen ? 'border-blue-500 ring-2 ring-blue-100' : '', buttonClass]"
				@click.stop="open"
			>
				<Calendar class="h-4 w-4 flex-shrink-0 text-gray-400" />
				<span :class="modelValue ? '' : 'text-gray-400'">{{ displayValue }}</span>
			</button>
		</template>
	</DatePickerPopover>
</template>
