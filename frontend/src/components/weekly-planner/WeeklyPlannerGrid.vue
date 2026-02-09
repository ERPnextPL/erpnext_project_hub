<template>
	<div class="weekly-grid bg-white">
		<!-- Header Row -->
		<div class="grid grid-cols-6 border-b sticky top-0 bg-white z-10">
			<div class="p-3 border-r font-semibold">Employee</div>
			<div
				v-for="(date, index) in weekDates"
				:key="date"
				class="p-3 border-r text-center"
				:class="{ 'border-r-0': index === weekDates.length - 1 }"
			>
				<div class="font-semibold">{{ dayName(date) }}</div>
				<div class="text-xs text-gray-500">{{ formatDate(date) }}</div>
			</div>
		</div>

		<!-- Loading State -->
		<div v-if="loading" class="flex items-center justify-center p-8">
			<div class="text-gray-400">Loading...</div>
		</div>

		<!-- Empty State -->
		<div v-else-if="employees.length === 0" class="flex items-center justify-center p-8">
			<div class="text-gray-400 text-center">
				<div class="text-4xl mb-2">👥</div>
				<div>No employees found</div>
			</div>
		</div>

		<!-- Employee Rows -->
		<div
			v-else
			v-for="employee in employees"
			:key="employee.name"
			class="grid grid-cols-6 border-b hover:bg-gray-50"
		>
			<!-- Employee Info Cell -->
			<div class="p-3 border-r">
				<div class="font-medium text-sm">{{ employee.employee_name }}</div>
				<div class="text-xs text-gray-500">{{ employee.designation }}</div>
				<div class="mt-2">
					<CapacityBadge :employee="employee.name" />
				</div>
			</div>

			<!-- Day Cells -->
			<DayCell
				v-for="(date, index) in weekDates"
				:key="`${employee.name}-${date}`"
				:employee="employee.name"
				:date="date"
				:assignments="getAssignmentsForCell(employee.name, date)"
				:total-hours="getHoursForCell(employee.name, date)"
				:class="{ 'border-r-0': index === weekDates.length - 1 }"
				@drop="emit('drop', { employee: employee.name, date: $event })"
				@update-hours="emit('update-hours', $event)"
				@delete="emit('delete', $event)"
			/>
		</div>
	</div>
</template>

<script setup>
import { defineProps, defineEmits } from "vue";
import DayCell from "./DayCell.vue";
import CapacityBadge from "./CapacityBadge.vue";

const props = defineProps({
	employees: { type: Array, default: () => [] },
	weekDates: { type: Array, default: () => [] },
	assignments: { type: Array, default: () => [] },
	capacities: { type: Object, default: () => ({}) },
	loading: { type: Boolean, default: false },
});

const emit = defineEmits(["drop", "update-hours", "delete"]);

function getAssignmentsForCell(employee, date) {
	return props.assignments.filter(
		(a) => a.employee === employee && a.assignment_date === date
	);
}

function getHoursForCell(employee, date) {
	if (props.capacities[employee] && props.capacities[employee][date]) {
		return props.capacities[employee][date];
	}
	return 0;
}

function dayName(date) {
	const d = new Date(date);
	const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
	return days[d.getDay()];
}

function formatDate(date) {
	const d = new Date(date);
	return `${d.getMonth() + 1}/${d.getDate()}`;
}
</script>
