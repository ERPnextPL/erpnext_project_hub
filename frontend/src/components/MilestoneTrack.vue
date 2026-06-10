<script setup>
import { computed } from "vue";
import { Check, AlertTriangle, X as XIcon } from "lucide-vue-next";
import { useTaskStore } from "../stores/taskStore";
import { translate } from "../utils/translation";

const props = defineProps({
	milestones: { type: Array, default: () => [] },
});

const store = useTaskStore();

const HEALTH = {
	completed:   { bg: "#10b981", border: "#10b981", text: "#fff", line: "#10b981" },
	on_track:    { bg: "#3b82f6", border: "#3b82f6", text: "#fff", line: "#3b82f6" },
	at_risk:     { bg: "#f59e0b", border: "#f59e0b", text: "#fff", line: "#f59e0b" },
	overdue:     { bg: "#ef4444", border: "#ef4444", text: "#fff", line: "#ef4444" },
	no_deadline: { bg: "#ffffff", border: "#9ca3af", text: "#9ca3af", line: "#e5e7eb" },
	cancelled:   { bg: "#f3f4f6", border: "#d1d5db", text: "#9ca3af", line: "#e5e7eb" },
};

function nodeStyle(ms) {
	const c = HEALTH[ms.health] || HEALTH.no_deadline;
	return { backgroundColor: c.bg, borderColor: c.border, color: c.text };
}

function lineStyle(ms) {
	const c = HEALTH[ms.health] || HEALTH.no_deadline;
	return { backgroundColor: c.line };
}

function formatDate(str) {
	if (!str) return null;
	const [y, m, d] = str.split("-").map(Number);
	return new Date(y, m - 1, d).toLocaleDateString("pl-PL", { day: "numeric", month: "short" });
}

function isSelected(name) {
	return store.activeMilestoneFilter.includes(name);
}

function toggle(name) {
	store.setMilestoneFilter(name);
}

const HEALTH_LABELS = {
	completed:   () => translate("Completed"),
	on_track:    () => translate("On Track"),
	at_risk:     () => translate("At Risk"),
	overdue:     () => translate("Overdue"),
	no_deadline: () => translate("No Deadline"),
	cancelled:   () => translate("Cancelled"),
};

function healthLabel(h) {
	return (HEALTH_LABELS[h] || HEALTH_LABELS.no_deadline)();
}
</script>

<template>
	<div
		v-if="milestones.length"
		class="overflow-x-auto border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
	>
		<div class="flex items-start px-4 py-3 sm:px-6 lg:px-8" style="min-width: max-content">
			<template v-for="(ms, i) in milestones" :key="ms.name">
				<!-- Node -->
				<div class="flex flex-col items-center" style="width: 72px">
					<button
						class="h-8 w-8 flex-shrink-0 rounded-full border-2 flex items-center justify-center transition-all duration-150 focus:outline-none"
						:class="isSelected(ms.name) ? 'ring-2 ring-offset-2 ring-blue-400 scale-110' : 'hover:scale-110'"
						:style="nodeStyle(ms)"
						:title="`${ms.milestone_name || ms.name} · ${healthLabel(ms.health)}`"
						@click="toggle(ms.name)"
					>
						<Check v-if="ms.health === 'completed'" class="h-3.5 w-3.5" stroke-width="3" />
						<XIcon v-else-if="ms.health === 'cancelled'" class="h-3.5 w-3.5" stroke-width="3" />
						<AlertTriangle v-else-if="ms.health === 'overdue' || ms.health === 'at_risk'" class="h-3 w-3" stroke-width="2.5" />
						<span v-else class="text-[9px] font-bold leading-none">{{ ms.progress || 0 }}%</span>
					</button>

					<p
						class="mt-1.5 max-w-[68px] overflow-hidden text-ellipsis whitespace-nowrap text-center text-[11px] font-medium leading-tight"
						:class="isSelected(ms.name) ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'"
						:title="ms.milestone_name || ms.name"
					>
						{{ ms.milestone_name || ms.name }}
					</p>
					<p v-if="ms.milestone_date" class="mt-0.5 text-[10px] text-gray-400 dark:text-gray-500">
						{{ formatDate(ms.milestone_date) }}
					</p>
				</div>

				<!-- Connector line (not after last) -->
				<div
					v-if="i < milestones.length - 1"
					class="mt-[15px] h-0.5 flex-shrink-0"
					style="width: 20px"
					:style="lineStyle(ms)"
				></div>
			</template>
		</div>
	</div>
</template>
