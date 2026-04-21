<script setup>
import { Diamond, X } from "lucide-vue-next";
import MilestonePanel from "./MilestonePanel.vue";
import { translate } from "../utils/translation";

defineEmits(["close"]);
</script>

<template>
	<div class="flex h-full w-80 flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
		<div
			class="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700"
		>
			<div class="flex items-center gap-2">
				<Diamond class="h-4 w-4 text-purple-600 dark:text-purple-400" />
				<h3 class="text-sm font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">
					{{ translate("Milestones") }}
				</h3>
			</div>
			<button
				class="rounded p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
				:title="translate('Close')"
				@click="$emit('close')"
			>
				<X class="h-4 w-4" />
			</button>
		</div>

		<div class="min-h-0 flex-1 overflow-y-auto">
			<MilestonePanel />
		</div>
	</div>
</template>
