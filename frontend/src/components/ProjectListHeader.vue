<script setup>
import { translate } from "../utils/translation";

defineProps({
	sortable: { type: Boolean, default: false },
	sortField: { type: String, default: null },
	sortIcon: { type: Function, default: null },
	toggleSort: { type: Function, default: null },
});

const COLUMNS = [
	{ field: "project_name", label: translate("Project"), align: "text-left" },
	{ field: "percent_complete", label: translate("Progress") },
	{ field: "expected_end_date", label: translate("Deadline") },
	{ field: null, label: translate("Manager") },
	{ field: "task_count", label: translate("Tasks") },
];
</script>

<template>
	<div class="grid grid-cols-[minmax(0,2fr)_repeat(4,minmax(0,1fr))] gap-4 px-4 py-2.5 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
		<template v-for="col in COLUMNS" :key="col.label">
			<button
				v-if="sortable && col.field"
				:class="['flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-300', col.align || '']"
				@click="toggleSort(col.field)"
			>
				{{ col.label }}
				<component :is="sortIcon(col.field)" class="w-3 h-3" />
			</button>
			<span v-else>{{ col.label }}</span>
		</template>
	</div>
</template>
