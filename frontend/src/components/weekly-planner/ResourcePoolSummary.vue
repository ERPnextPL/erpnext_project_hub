<template>
	<div class="resource-pool-summary border-t bg-white">
		<div
			class="px-4 py-2 border-b bg-gray-50 flex items-center justify-between cursor-pointer"
			@click="isExpanded = !isExpanded"
		>
			<h3 class="font-semibold">Resource Pool Summary</h3>
			<span>{{ isExpanded ? "▼" : "▲" }}</span>
		</div>

		<div v-if="isExpanded" class="max-h-64 overflow-y-auto">
			<div v-if="data.length === 0" class="p-4 text-center text-gray-400">
				No data available
			</div>

			<div v-else class="grid grid-cols-3 gap-3 p-4">
				<div
					v-for="emp in sortedData"
					:key="emp.employee"
					class="border rounded p-3 hover:shadow-md cursor-pointer transition-shadow"
					:class="availabilityClass(emp.availability_percent)"
					@click="emit('select-employee', emp.employee)"
				>
					<div class="font-medium text-sm">{{ emp.employee_name }}</div>
					<div class="text-xs text-gray-500">{{ emp.designation }}</div>
					<div class="mt-2 text-sm">
						<div class="flex justify-between">
							<span>Available:</span>
							<span class="font-semibold">{{ emp.available.toFixed(1) }}h</span>
						</div>
						<div class="text-xs text-gray-500">
							{{ emp.availability_percent.toFixed(0) }}% free
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
	data: { type: Array, default: () => [] },
});

const emit = defineEmits(["select-employee"]);

const isExpanded = ref(true);

const sortedData = computed(() => {
	return [...props.data].sort((a, b) => b.available - a.available);
});

function availabilityClass(percent) {
	if (percent > 50) return "border-green-300 bg-green-50";
	if (percent > 25) return "border-yellow-300 bg-yellow-50";
	if (percent > 12) return "border-orange-300 bg-orange-50";
	return "border-red-300 bg-red-50";
}
</script>
