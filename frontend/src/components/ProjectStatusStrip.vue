<script setup>
import { ref, computed } from "vue";
import { translate } from "../utils/translation";

const props = defineProps({
	project: { type: Object, default: null },
});

// --- Ring: remaining / elapsed time ---
function parseDate(str) {
	const [y, m, d] = str.split("-").map(Number);
	return new Date(y, m - 1, d);
}

const timeInfo = computed(() => {
	const endStr = props.project?.expected_end_date;
	const startStr = props.project?.expected_start_date;
	if (!endStr) return { days: null, remainingPct: 100, type: "none" };

	const end = parseDate(endStr);
	const today = new Date();
	today.setHours(0, 0, 0, 0);
	const days = Math.round((end - today) / 86400000);

	let totalDays = 100;
	if (startStr) {
		const start = parseDate(startStr);
		totalDays = Math.max(Math.round((end - start) / 86400000), 1);
	}
	const remainingPct = Math.max(0, Math.min(100, (days / totalDays) * 100));

	if (days < 0) return { days: Math.abs(days), remainingPct: 0, type: "overdue" };
	if (days === 0) return { days: 0, remainingPct, type: "today" };
	if (days <= 7) return { days, remainingPct, type: "critical" };
	if (days <= 30) return { days, remainingPct, type: "soon" };
	return { days, remainingPct, type: "ok" };
});

const RING_COLORS = {
	none: "#9ca3af",
	today: "#f97316",
	overdue: "#ef4444",
	critical: "#f87171",
	soon: "#f97316",
	ok: "#22c55e",
};

const ringColor = computed(() => RING_COLORS[timeInfo.value.type]);

// SVG ring: r=13, circumference ≈ 81.68
const CIRC = 2 * Math.PI * 13;
const ringDash = computed(() => {
	const fill = (timeInfo.value.remainingPct / 100) * CIRC;
	return `${fill} ${CIRC}`;
});

const timeLabel = computed(() => {
	const { type, days } = timeInfo.value;
	if (type === "none") return translate("No end date");
	if (type === "overdue") return `${days}d ${translate("overdue")}`;
	if (type === "today") return translate("Last day!");
	return `${days} ${translate("days left")}`;
});

// --- Task progress ---
const taskPct = computed(() => Math.round(props.project?.percent_complete || 0));
const taskTotal = computed(() => props.project?.total_tasks || 0);
const taskDone = computed(() => props.project?.completed_tasks || 0);

const barColor = computed(() => {
	const p = taskPct.value;
	if (p >= 100) return "bg-green-500";
	if (p >= 50) return "bg-blue-500";
	return "bg-gray-400 dark:bg-gray-500";
});
</script>

<template>
	<div
		v-if="project"
		class="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
	>
		<!-- Main strip (always visible) -->
		<div
			class="flex items-center gap-3 px-4 py-2 sm:px-6 lg:px-8"
			style="min-height: 44px"
		>
			<!-- 1. Time ring -->
			<div class="flex flex-shrink-0 items-center gap-2">
				<svg width="32" height="32" viewBox="0 0 32 32" class="flex-shrink-0">
					<!-- Background ring -->
					<circle
						cx="16" cy="16" r="13"
						fill="none"
						class="stroke-gray-200 dark:stroke-gray-700"
						stroke-width="3"
					/>
					<!-- Remaining time arc -->
					<circle
						cx="16" cy="16" r="13"
						fill="none"
						:stroke="ringColor"
						stroke-width="3"
						stroke-linecap="round"
						:stroke-dasharray="ringDash"
						transform="rotate(-90 16 16)"
					/>
				</svg>
				<span
					class="text-xs font-medium whitespace-nowrap"
					:style="{ color: ringColor }"
				>
					{{ timeLabel }}
				</span>
			</div>

			<!-- Divider -->
			<div class="h-4 w-px flex-shrink-0 bg-gray-200 dark:bg-gray-700"></div>

			<!-- 2. Task progress bar -->
			<div class="flex min-w-0 flex-1 items-center gap-2">
				<div
					class="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
				>
					<div
						class="h-full rounded-full transition-all duration-500"
						:class="barColor"
						:style="{ width: taskPct + '%' }"
					></div>
				</div>
				<span class="flex-shrink-0 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
					<template v-if="taskTotal > 0">
						{{ taskDone }}/{{ taskTotal }} &middot; {{ taskPct }}%
					</template>
					<template v-else>{{ taskPct }}%</template>
				</span>
			</div>

		</div>
	</div>
</template>
