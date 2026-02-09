<template>
	<div class="header bg-white border-b p-4">
		<div class="flex items-center justify-between">
			<!-- Week Navigation -->
			<div class="flex items-center gap-4">
				<button
					@click="emit('week-change', 'prev')"
					class="px-3 py-2 border rounded hover:bg-gray-50"
				>
					← Previous
				</button>

				<div class="text-lg font-semibold">
					{{ weekLabel }}
				</div>

				<button
					@click="emit('week-change', 'next')"
					class="px-3 py-2 border rounded hover:bg-gray-50"
				>
					Next →
				</button>

				<button
					@click="emit('week-change', 'today')"
					class="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
				>
					Today
				</button>
			</div>

			<!-- Actions -->
			<div class="flex items-center gap-2">
				<button
					@click="emit('toggle-resource-pool')"
					class="px-3 py-2 border rounded hover:bg-gray-50"
				>
					📊 Resource Pool
				</button>

				<button
					@click="emit('generate-timesheets')"
					class="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600"
				>
					⏱️ Generate Timesheets
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { useWeeklyPlanningStore } from "../../stores/weeklyPlanningStore";

const emit = defineEmits(["week-change", "filter-change", "toggle-resource-pool", "generate-timesheets"]);
const store = useWeeklyPlanningStore();

const weekLabel = computed(() => {
	if (!store.currentWeekStart) return "";

	const start = new Date(store.currentWeekStart);
	const end = new Date(start);
	end.setDate(end.getDate() + 4); // Friday

	const options = { month: "short", day: "numeric" };
	const startYear = start.getFullYear();
	const endYear = end.getFullYear();
	const startLabel = start.toLocaleDateString("en-US", options);
	const endLabel = end.toLocaleDateString("en-US", options);

	if (startYear !== endYear) {
		return `${startLabel}, ${startYear} - ${endLabel}, ${endYear}`;
	}

	return `${startLabel} - ${endLabel}, ${startYear}`;
});
</script>
