<template>
	<div class="capacity-badge text-xs px-2 py-1 rounded" :class="colorClass">
		{{ totalHours.toFixed(1) }}h / 40h
	</div>
</template>

<script setup>
import { computed, defineProps } from "vue";
import { useWeeklyPlanningStore } from "../../stores/weeklyPlanningStore";

const props = defineProps({
	employee: { type: String, required: true },
});

const store = useWeeklyPlanningStore();

const totalHours = computed(() => {
	const summary = store.employeeCapacitySummary[props.employee];
	return summary ? summary.allocated : 0;
});

const colorClass = computed(() => {
	if (totalHours.value > 42) return "bg-red-100 text-red-700";
	if (totalHours.value > 40) return "bg-orange-100 text-orange-700";
	if (totalHours.value >= 32) return "bg-blue-100 text-blue-700";
	return "bg-green-100 text-green-700";
});
</script>
