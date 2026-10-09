<script setup>
import { Diamond, X } from "lucide-vue-next";
import MilestonePanel from "./MilestonePanel.vue";
import { useTaskStore } from "../stores/taskStore";
import { translate } from "../utils/translation";

defineEmits(["close"]);

const store = useTaskStore();
</script>

<template>
	<div class="border-b border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
		<!-- Dropdown header -->
		<div class="flex items-center justify-between border-b border-gray-100 px-4 py-2.5 dark:border-gray-700 sm:px-6 lg:px-8">
			<div class="flex items-center gap-2">
				<Diamond class="h-4 w-4 text-purple-600 dark:text-purple-400" />
				<span class="text-sm font-semibold text-gray-700 dark:text-gray-300">
					{{ translate("Milestones") }}
				</span>
				<span
					v-if="store.milestones.length"
					class="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500 dark:bg-gray-700 dark:text-gray-400"
				>
					{{ store.milestones.length }}
				</span>
			</div>
			<button
				class="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
				:title="translate('Close')"
				@click="$emit('close')"
			>
				<X class="h-4 w-4" />
			</button>
		</div>

		<!-- Panel content -->
		<div class="max-h-80 overflow-y-auto">
			<MilestonePanel :hide-header="true" />
		</div>
	</div>
</template>
