<template>
	<div
		class="day-cell p-2 border-r min-h-24 relative"
		:class="[dropZoneClass, capacityClass]"
		@dragover.prevent="handleDragOver"
		@dragleave="handleDragLeave"
		@drop.prevent="handleDrop"
	>
		<!-- Capacity Progress Bar -->
		<div class="capacity-bar h-1 mb-2 rounded-full bg-gray-200">
			<div
				class="h-full rounded-full transition-all"
				:class="progressColorClass"
				:style="{ width: capacityPercent + '%' }"
			/>
		</div>

		<!-- Assigned Tasks -->
		<div class="space-y-1">
			<TaskCard
				v-for="assignment in assignments"
				:key="assignment.name"
				:assignment="assignment"
				@update-hours="emit('update-hours', $event)"
				@delete="emit('delete', $event)"
			/>
		</div>

		<!-- Total Hours Badge -->
		<div
			v-if="totalHours > 0"
			class="text-xs text-center mt-1 font-medium"
			:class="totalHoursColorClass"
		>
			{{ totalHours.toFixed(1) }}h
		</div>

		<!-- Empty State -->
		<div
			v-if="assignments.length === 0"
			class="text-xs text-gray-300 text-center absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
		>
			Drop here
		</div>
	</div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from "vue";
import TaskCard from "./TaskCard.vue";

const props = defineProps({
	employee: { type: String, required: true },
	date: { type: String, required: true },
	assignments: { type: Array, default: () => [] },
	totalHours: { type: Number, default: 0 },
});

const emit = defineEmits(["drop", "update-hours", "delete"]);

const isDragOver = ref(false);

const capacityPercent = computed(() => {
	const percent = (props.totalHours / 8) * 100;
	return Math.min(percent, 100);
});

const progressColorClass = computed(() => {
	if (props.totalHours > 10) return "bg-red-500";
	if (props.totalHours > 8) return "bg-orange-500";
	if (props.totalHours >= 6) return "bg-blue-500";
	return "bg-green-500";
});

const capacityClass = computed(() => {
	if (props.totalHours > 10) return "bg-red-50";
	if (props.totalHours > 8) return "bg-orange-50";
	return "";
});

const totalHoursColorClass = computed(() => {
	if (props.totalHours > 10) return "text-red-700";
	if (props.totalHours > 8) return "text-orange-700";
	if (props.totalHours >= 6) return "text-blue-700";
	return "text-green-700";
});

const dropZoneClass = computed(() => {
	return isDragOver.value ? "ring-2 ring-blue-400 bg-blue-50" : "";
});

function handleDragOver(event) {
	isDragOver.value = true;
	event.dataTransfer.dropEffect = "move";
}

function handleDragLeave() {
	isDragOver.value = false;
}

function handleDrop(event) {
	isDragOver.value = false;

	try {
		const taskData = JSON.parse(event.dataTransfer.getData("text/plain"));
		emit("drop", props.date);
	} catch (err) {
		console.error("Error handling drop:", err);
	}
}
</script>
