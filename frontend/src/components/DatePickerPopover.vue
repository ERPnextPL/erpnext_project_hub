<script>
import { ref } from "vue";

const activeDatePickerId = ref(null);
</script>

<script setup>
import { computed, onUnmounted, ref, watch } from "vue";
import { ChevronLeft, ChevronRight } from "lucide-vue-next";
import { getRealWindow, translate } from "../utils/translation";

const props = defineProps({
	id: {
		type: String,
		required: true,
	},
	modelValue: {
		type: String,
		default: "",
	},
	disabled: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["update:modelValue"]);
const realWindow = getRealWindow();
const datePickerPosition = ref({ left: 0, top: 0 });
const pickerMonth = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1));

const isOpen = computed(() => activeDatePickerId.value === props.id);

const weekdayLabels = computed(() => {
	const monday = new Date(2024, 0, 1);
	return Array.from({ length: 7 }, (_, index) => {
		const date = new Date(monday);
		date.setDate(monday.getDate() + index);
		return date.toLocaleDateString(undefined, { weekday: "short" });
	});
});

const pickerMonthLabel = computed(() =>
	pickerMonth.value.toLocaleDateString(undefined, { month: "long", year: "numeric" })
);

const pickerDays = computed(() => {
	const month = pickerMonth.value;
	const firstDay = new Date(month.getFullYear(), month.getMonth(), 1);
	const mondayOffset = (firstDay.getDay() + 6) % 7;
	const startDate = new Date(firstDay);
	startDate.setDate(firstDay.getDate() - mondayOffset);

	return Array.from({ length: 42 }, (_, index) => {
		const date = new Date(startDate);
		date.setDate(startDate.getDate() + index);
		return {
			date,
			dateStr: toLocalDateString(date),
			isCurrentMonth: date.getMonth() === month.getMonth(),
		};
	});
});

function toLocalDateString(date) {
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, "0");
	const day = String(date.getDate()).padStart(2, "0");
	return `${year}-${month}-${day}`;
}

function parseDate(value) {
	if (!value) return new Date();
	const [year, month, day] = value.slice(0, 10).split("-").map(Number);
	return new Date(year, month - 1, day);
}

function isToday(dateStr) {
	return dateStr === toLocalDateString(new Date());
}

function isSelectedDate(dateStr) {
	return dateStr === props.modelValue;
}

function openPicker(event) {
	if (props.disabled) return;
	if (isOpen.value) {
		closePicker();
		return;
	}

	const currentDate = parseDate(props.modelValue);
	pickerMonth.value = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);

	const rect = event.currentTarget.getBoundingClientRect();
	const pickerWidth = 288;
	const pickerHeight = 360;
	const viewportWidth = realWindow?.innerWidth || 1024;
	const viewportHeight = realWindow?.innerHeight || 768;
	const left = Math.min(rect.left, viewportWidth - pickerWidth - 12);
	const top =
		rect.bottom + pickerHeight <= viewportHeight
			? rect.bottom + 8
			: Math.max(12, rect.top - pickerHeight - 8);

	datePickerPosition.value = { left: Math.max(12, left), top };
	activeDatePickerId.value = props.id;
}

function closePicker() {
	if (isOpen.value) {
		activeDatePickerId.value = null;
	}
}

function changePickerMonth(offset) {
	pickerMonth.value = new Date(
		pickerMonth.value.getFullYear(),
		pickerMonth.value.getMonth() + offset,
		1
	);
}

function selectDate(dateStr) {
	if (dateStr !== props.modelValue) {
		emit("update:modelValue", dateStr);
	}
	closePicker();
}

function selectToday() {
	selectDate(toLocalDateString(new Date()));
}

function clearDate() {
	selectDate("");
}

function handleDocumentClick(event) {
	if (isOpen.value && !event.target.closest(".date-picker-popover")) {
		closePicker();
	}
}

watch(isOpen, (open) => {
	if (open) {
		document.addEventListener("click", handleDocumentClick);
	} else {
		document.removeEventListener("click", handleDocumentClick);
	}
});

onUnmounted(() => {
	document.removeEventListener("click", handleDocumentClick);
	if (isOpen.value) closePicker();
});
</script>

<template>
	<slot name="trigger" :open="openPicker" :is-open="isOpen" />

	<Teleport to="body">
		<Transition name="fade">
			<div
				v-if="isOpen"
				class="date-picker-popover fixed z-50 w-72 rounded-2xl border border-gray-200 bg-white p-3 shadow-2xl dark:border-gray-700 dark:bg-gray-900"
				:style="{
					left: `${datePickerPosition.left}px`,
					top: `${datePickerPosition.top}px`,
				}"
				@click.stop
			>
				<div class="flex items-center justify-between px-1 pb-3">
					<button
						type="button"
						class="rounded-lg p-1.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-gray-100"
						:title="translate('Previous month')"
						@click="changePickerMonth(-1)"
					>
						<ChevronLeft class="h-4 w-4" />
					</button>
					<strong class="text-sm font-semibold capitalize text-gray-900 dark:text-gray-100">
						{{ pickerMonthLabel }}
					</strong>
					<button
						type="button"
						class="rounded-lg p-1.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-gray-100"
						:title="translate('Next month')"
						@click="changePickerMonth(1)"
					>
						<ChevronRight class="h-4 w-4" />
					</button>
				</div>

				<div class="grid grid-cols-7 gap-1 pb-1">
					<span
						v-for="weekday in weekdayLabels"
						:key="weekday"
						class="py-1 text-center text-[10px] font-semibold uppercase text-gray-400 dark:text-gray-500"
					>
						{{ weekday }}
					</span>
				</div>

				<div class="grid grid-cols-7 gap-1">
					<button
						v-for="day in pickerDays"
						:key="day.dateStr"
						type="button"
						:class="[
							'h-8 rounded-lg text-xs font-medium transition-colors',
							day.isCurrentMonth
								? 'text-gray-700 hover:bg-blue-50 dark:text-gray-200 dark:hover:bg-blue-950'
								: 'text-gray-300 hover:bg-gray-50 dark:text-gray-600 dark:hover:bg-gray-800',
							isToday(day.dateStr) && !isSelectedDate(day.dateStr)
								? 'ring-1 ring-blue-500 ring-inset'
								: '',
							isSelectedDate(day.dateStr)
								? 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600'
								: '',
						]"
						:aria-label="day.dateStr"
						@click="selectDate(day.dateStr)"
					>
						{{ day.date.getDate() }}
					</button>
				</div>

				<div class="mt-3 flex items-center justify-between border-t border-gray-100 pt-3 dark:border-gray-800">
					<button
						type="button"
						class="text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
						@click="selectToday"
					>
						{{ translate("Today") }}
					</button>
					<button
						type="button"
						class="text-xs text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
						@click="clearDate"
					>
						{{ translate("Clear") }}
					</button>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>
