<template>
	<div
		v-if="show"
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
		@click.self="handleCancel"
	>
		<div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
			<!-- Header -->
			<div class="px-6 py-4 border-b">
				<h3 class="text-lg font-semibold">Allocate Hours</h3>
			</div>

			<!-- Body -->
			<div class="px-6 py-4 space-y-4">
				<!-- Task Info -->
				<div class="bg-blue-50 p-3 rounded">
					<div class="font-medium">{{ task?.subject || "Task" }}</div>
					<div class="text-sm text-gray-600">
						Expected: {{ task?.expected_time || 0 }}h
					</div>
				</div>

				<!-- Hours Input -->
				<div>
					<label class="block text-sm font-medium mb-1">
						Hours to allocate
					</label>
					<input
						ref="hoursInput"
						v-model="hours"
						type="number"
						step="0.5"
						min="0.5"
						max="24"
						class="w-full border rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
						@keyup.enter="handleConfirm"
						@keyup.esc="handleCancel"
					/>
				</div>

				<!-- Current Day Summary -->
				<div class="text-sm space-y-1">
					<div class="flex justify-between">
						<span>Current day total:</span>
						<span :class="currentHoursClass">{{ currentHours }}h</span>
					</div>
					<div class="flex justify-between">
						<span>After allocation:</span>
						<span :class="afterAllocationClass">{{ afterAllocation.toFixed(1) }}h</span>
					</div>
				</div>

				<!-- Warning -->
				<div
					v-if="afterAllocation > 8"
					class="bg-orange-50 border-l-4 border-orange-500 p-3"
				>
					<p class="text-sm text-orange-700">
						⚠️ This allocation will exceed the 8-hour daily target
					</p>
				</div>
			</div>

			<!-- Footer -->
			<div class="px-6 py-4 border-t flex justify-end gap-2">
				<button
					@click="handleCancel"
					class="px-4 py-2 border rounded hover:bg-gray-50"
				>
					Cancel
				</button>
				<button
					@click="handleConfirm"
					class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
				>
					Confirm
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";

const props = defineProps({
	show: { type: Boolean, default: false },
	task: { type: Object, default: null },
	employee: { type: String, default: null },
	date: { type: String, default: null },
	currentHours: { type: Number, default: 0 },
});

const emit = defineEmits(["update:show", "confirm"]);

const hours = ref(1);
const hoursInput = ref(null);

// Auto-fill hours based on task expected_time (capped at 8)
watch(
	() => props.show,
	(newVal) => {
		if (newVal && props.task) {
			const expectedTime = props.task.expected_time || 8;
			hours.value = Math.min(expectedTime, 8);

			// Focus input
			nextTick(() => {
				hoursInput.value?.focus();
				hoursInput.value?.select();
			});
		}
	}
);

const afterAllocation = computed(() => {
	return props.currentHours + parseFloat(hours.value || 0);
});

const currentHoursClass = computed(() => {
	if (props.currentHours > 10) return "text-red-600 font-semibold";
	if (props.currentHours > 8) return "text-orange-600 font-semibold";
	return "text-gray-700";
});

const afterAllocationClass = computed(() => {
	if (afterAllocation.value > 10) return "text-red-600 font-semibold";
	if (afterAllocation.value > 8) return "text-orange-600 font-semibold";
	return "text-green-600 font-semibold";
});

function handleConfirm() {
	if (!hours.value || parseFloat(hours.value) <= 0) {
		alert("Please enter a valid number of hours");
		return;
	}

	emit("confirm", parseFloat(hours.value));
	emit("update:show", false);
}

function handleCancel() {
	emit("update:show", false);
}
</script>
