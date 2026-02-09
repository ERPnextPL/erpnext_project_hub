<template>
	<div
		class="task-card text-xs bg-white border rounded p-2 hover:shadow-sm cursor-pointer group"
		:class="statusColorClass"
	>
		<div class="flex items-start justify-between gap-1">
			<div class="flex-1 min-w-0 truncate" :title="assignment.task_subject">
				{{ assignment.task_subject }}
			</div>
			<div class="font-semibold text-blue-600">
				{{ assignment.allocated_hours }}h
			</div>
		</div>

		<!-- Actions (show on hover) -->
		<div class="flex gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
			<button
				@click.stop="handleEdit"
				class="text-xs text-blue-600 hover:underline"
			>
				Edit
			</button>
			<button
				@click.stop="handleDelete"
				class="text-xs text-red-600 hover:underline"
			>
				Delete
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, defineProps, defineEmits } from "vue";

const props = defineProps({
	assignment: { type: Object, required: true },
});

const emit = defineEmits(["update-hours", "delete"]);

const statusColorClass = computed(() => {
	const status = props.assignment.status;
	if (status === "Completed") return "border-green-300 bg-green-50";
	if (status === "In Progress") return "border-blue-300 bg-blue-50";
	if (status === "Cancelled") return "border-gray-300 bg-gray-50";
	return "border-gray-200";
});

function handleEdit() {
	const hours = prompt("Enter new hours:", props.assignment.allocated_hours);
	if (hours && !isNaN(parseFloat(hours))) {
		emit("update-hours", {
			assignmentId: props.assignment.name,
			hours: parseFloat(hours),
		});
	}
}

function handleDelete() {
	emit("delete", props.assignment.name);
}
</script>
