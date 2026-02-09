<template>
	<div class="task-pool h-full flex flex-col">
		<div class="p-4 border-b bg-white sticky top-0">
			<h3 class="font-semibold text-lg">Unassigned Tasks</h3>
			<p class="text-xs text-gray-500">Drag tasks to assign</p>
		</div>

		<div v-if="loading" class="flex-1 flex items-center justify-center">
			<div class="text-gray-400">Loading tasks...</div>
		</div>

		<div v-else-if="tasks.length === 0" class="flex-1 flex items-center justify-center">
			<div class="text-gray-400 text-center p-4">
				<div class="text-4xl mb-2">📋</div>
				<div>No tasks available</div>
			</div>
		</div>

		<div v-else class="flex-1 overflow-y-auto p-2 space-y-2">
			<div
				v-for="task in tasks"
				:key="task.name"
				:draggable="true"
				@dragstart="handleDragStart($event, task)"
				@dragend="handleDragEnd"
				class="task-card p-3 bg-white border rounded cursor-grab hover:shadow-md transition-shadow active:cursor-grabbing"
			>
				<div class="flex items-start justify-between">
					<div class="flex-1 min-w-0">
						<div class="font-medium text-sm truncate" :title="task.subject">
							{{ task.subject }}
						</div>
						<div class="text-xs text-gray-500 mt-1">
							{{ task.project_name || task.project }}
						</div>
					</div>
					<div class="ml-2 text-xs font-semibold text-blue-600">
						{{ task.expected_time }}h
					</div>
				</div>

				<div class="flex items-center gap-2 mt-2">
					<span
						v-if="task.priority"
						class="text-xs px-2 py-0.5 rounded"
						:class="priorityClass(task.priority)"
					>
						{{ task.priority }}
					</span>
					<span class="text-xs px-2 py-0.5 rounded bg-gray-100">
						{{ task.status }}
					</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { defineProps, defineEmits } from "vue";

const props = defineProps({
	tasks: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
});

const emit = defineEmits(["dragstart"]);

function handleDragStart(event, task) {
	event.dataTransfer.effectAllowed = "move";
	event.dataTransfer.setData("text/plain", JSON.stringify(task));
	emit("dragstart", task);
}

function handleDragEnd() {
	// Clean up drag state if needed
}

function priorityClass(priority) {
	const classes = {
		High: "bg-red-100 text-red-700",
		Medium: "bg-yellow-100 text-yellow-700",
		Low: "bg-green-100 text-green-700",
		Urgent: "bg-purple-100 text-purple-700",
	};
	return classes[priority] || "bg-gray-100";
}
</script>
