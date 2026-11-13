<script setup>
import { ref, computed, onMounted, onBeforeUnmount, onUpdated, nextTick, watch, toRaw } from "vue";
import { Calendar, ChevronLeft, ChevronRight, Diamond } from "lucide-vue-next";
import { translate } from "../utils/translation";
import { TASK_STATUSES, getStatusConfig } from "../utils/taskStatus";
import { useTaskStore } from "../stores/taskStore";
import BlockedToggle from "./atoms/BlockedToggle.vue";

const t = translate;

const props = defineProps({
	tasks: {
		type: Array,
		required: true,
	},
	projectId: {
		type: String,
		required: true,
	},
});

const emit = defineEmits(["task-click"]);

// Timeline state
const viewStartDate = ref(new Date());
const RANGE_OPTIONS = [7, 14, 30, 90];
const RANGE_STORAGE_KEY = "projectHub.timeline.daysToShow";
function loadSavedRange() {
	try {
		const saved = Number(localStorage.getItem(RANGE_STORAGE_KEY));
		return RANGE_OPTIONS.includes(saved) ? saved : 30;
	} catch {
		return 30;
	}
}
const daysToShow = ref(loadSavedRange());
const isCompact = computed(() => daysToShow.value > 45);
const navigationStep = computed(() => (daysToShow.value >= 90 ? 28 : daysToShow.value >= 30 ? 14 : 7));

function setRange(days) {
	daysToShow.value = days;
	try {
		localStorage.setItem(RANGE_STORAGE_KEY, String(days));
	} catch {
		/* storage unavailable */
	}
}

// Status colors - resolved from the shared status config
const statusColors = Object.fromEntries(
	TASK_STATUSES.map((status) => [status, getStatusConfig(status).dot])
);

// Priority colors for border
const priorityColors = {
	Urgent: "border-red-500",
	High: "border-orange-500",
	Medium: "border-yellow-500",
	Low: "border-gray-300",
};

// Get tasks with dates for timeline
const timelineTasks = computed(() => {
	return props.tasks.filter((task) => task.exp_start_date || task.exp_end_date);
});

// Generate date headers
const dateHeaders = computed(() => {
	const headers = [];
	const start = new Date(viewStartDate.value);
	start.setHours(0, 0, 0, 0);

	for (let i = 0; i < daysToShow.value; i++) {
		const date = new Date(start);
		date.setDate(start.getDate() + i);
		headers.push({
			date: date,
			// Two-letter Polish abbreviations: "niedz." / "śr." do not fit a day column.
			dayOfWeek: ["Nd", "Pn", "Wt", "Śr", "Cz", "Pt", "So"][date.getDay()],
			dayName: date.toLocaleDateString("pl-PL", { weekday: "long" }),
			dayOfMonth: date.getDate(),
			month: date.toLocaleDateString("pl-PL", { month: "short" }),
			isWeekend: date.getDay() === 0 || date.getDay() === 6,
			isToday: isSameDay(date, new Date()),
		});
	}
	return headers;
});

const DAY_MS = 24 * 60 * 60 * 1000;

// Parse "YYYY-MM-DD[ HH:MM:SS]" as a local calendar day (no timezone shift)
function parseLocalDay(value) {
	if (!value) return null;
	const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value));
	if (!m) {
		const d = new Date(value);
		if (isNaN(d)) return null;
		d.setHours(0, 0, 0, 0);
		return d;
	}
	return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
}

function formatDay(date) {
	const mm = String(date.getMonth() + 1).padStart(2, "0");
	const dd = String(date.getDate()).padStart(2, "0");
	return `${date.getFullYear()}-${mm}-${dd}`;
}

function addDays(date, days) {
	const d = new Date(date);
	d.setDate(d.getDate() + days);
	return d;
}

function dayDiff(a, b) {
	return Math.round((a - b) / DAY_MS);
}

function isSameDay(d1, d2) {
	return (
		d1.getFullYear() === d2.getFullYear() &&
		d1.getMonth() === d2.getMonth() &&
		d1.getDate() === d2.getDate()
	);
}

// Calculate task bar position and width
function getTaskBarStyle(task) {
	const startDate = new Date(viewStartDate.value);
	startDate.setHours(0, 0, 0, 0);
	const endViewDate = new Date(startDate);
	endViewDate.setDate(startDate.getDate() + daysToShow.value);

	const shown = withPendingDates(task);
	const taskStart = parseLocalDay(shown.exp_start_date);
	const taskEnd = parseLocalDay(shown.exp_end_date);

	// If no dates, skip
	if (!taskStart && !taskEnd) return null;

	// Calculate effective start and end
	let effectiveStart = taskStart || taskEnd;
	let effectiveEnd = taskEnd || taskStart;

	// Ensure start is before end
	if (effectiveStart > effectiveEnd) {
		[effectiveStart, effectiveEnd] = [effectiveEnd, effectiveStart];
	}

	// Live preview while dragging / resizing
	if (drag.value && drag.value.taskName === task.name && drag.value.moved) {
		const range = computeDraggedRange(drag.value, effectiveStart, effectiveEnd);
		effectiveStart = range.start;
		effectiveEnd = range.end;
	}

	// Check if task is visible in current view
	if (effectiveEnd < startDate || effectiveStart > endViewDate) {
		return null;
	}

	// Calculate position
	const dayWidth = 100 / daysToShow.value;
	const startOffset = Math.max(0, (effectiveStart - startDate) / (1000 * 60 * 60 * 24));
	const endOffset = Math.min(
		daysToShow.value,
		(effectiveEnd - startDate) / (1000 * 60 * 60 * 24) + 1
	);

	const left = startOffset * dayWidth;
	const width = Math.max((endOffset - startOffset) * dayWidth, dayWidth * 0.5);

	return {
		left: `${left}%`,
		width: `${width}%`,
	};
}

// ---- Drag to move / resize ----
const drag = ref(null);
// Dates saved optimistically: the bar stays where it was dropped until the API answers
const pendingDates = ref({});

function withPendingDates(task) {
	const pending = pendingDates.value[task.name];
	return pending ? { ...task, ...pending } : task;
}
const justDragged = ref(false);
const DRAG_THRESHOLD_PX = 4;

function computeDraggedRange(d, start, end) {
	let newStart = start;
	let newEnd = end;
	if (d.mode === "move") {
		newStart = addDays(start, d.deltaDays);
		newEnd = addDays(end, d.deltaDays);
	} else if (d.mode === "resize-start") {
		newStart = addDays(start, d.deltaDays);
		if (newStart > end) newStart = end;
	} else if (d.mode === "resize-end") {
		newEnd = addDays(end, d.deltaDays);
		if (newEnd < start) newEnd = start;
	}
	return { start: newStart, end: newEnd };
}

function startDrag(event, task, mode) {
	if (event.button !== undefined && event.button !== 0) return;
	const area = event.currentTarget.closest("[data-timeline-area]");
	if (!area) return;
	const dayWidthPx = area.getBoundingClientRect().width / daysToShow.value;
	if (!dayWidthPx) return;
	event.preventDefault();
	event.stopPropagation();

	drag.value = {
		taskName: task.name,
		mode,
		startX: event.clientX,
		dayWidthPx,
		deltaDays: 0,
		moved: false,
	};
	window.addEventListener("pointermove", onDragMove);
	window.addEventListener("pointerup", onDragEnd);
	window.addEventListener("pointercancel", cancelDrag);
}

function onDragMove(event) {
	const d = drag.value;
	if (!d) return;
	const dx = event.clientX - d.startX;
	if (!d.moved && Math.abs(dx) < DRAG_THRESHOLD_PX) return;
	d.moved = true;
	d.deltaDays = Math.round(dx / d.dayWidthPx);
}

function removeDragListeners() {
	window.removeEventListener("pointermove", onDragMove);
	window.removeEventListener("pointerup", onDragEnd);
	window.removeEventListener("pointercancel", cancelDrag);
}

function cancelDrag() {
	removeDragListeners();
	drag.value = null;
}

async function onDragEnd() {
	const d = drag.value;
	removeDragListeners();
	if (!d) return;
	drag.value = null;
	if (!d.moved) return;

	// Swallow the click that follows a drag so the detail panel does not open
	justDragged.value = true;
	setTimeout(() => (justDragged.value = false), 0);

	if (d.deltaDays === 0) return;
	const task = props.tasks.find((t) => t.name === d.taskName);
	if (!task) return;

	let start = parseLocalDay(withPendingDates(task).exp_start_date);
	let end = parseLocalDay(withPendingDates(task).exp_end_date);
	if (!start && !end) return;
	const hadStart = !!start;
	const hadEnd = !!end;
	start = start || end;
	end = end || start;
	if (start > end) [start, end] = [end, start];

	const range = computeDraggedRange(d, start, end);
	const updates = {};
	if (d.mode === "move") {
		if (hadStart) updates.exp_start_date = formatDay(range.start);
		if (hadEnd) updates.exp_end_date = formatDay(range.end);
	} else {
		updates.exp_start_date = formatDay(range.start);
		updates.exp_end_date = formatDay(range.end);
	}

	pendingDates.value = { ...pendingDates.value, [task.name]: updates };
	try {
		await store.updateTask(task.name, updates);
	} catch (error) {
		console.error("Failed to update task dates:", error);
	} finally {
		// A newer drag of the same task may have replaced this entry while the
		// save was running: leave that one in place until its own save returns.
		// pendingDates is deep-reactive: compare the raw object, not its proxy.
		if (toRaw(pendingDates.value[task.name]) === updates) {
			const { [task.name]: _done, ...rest } = pendingDates.value;
			pendingDates.value = rest;
		}
	}
}

// ---- Dependency arrows ----
const rowsRef = ref(null);
const arrows = ref([]);
let resizeObserver = null;

function taskDates(task) {
	const shown = withPendingDates(task);
	let start = parseLocalDay(shown.exp_start_date);
	let end = parseLocalDay(shown.exp_end_date);
	if (!start && !end) return null;
	start = start || end;
	end = end || start;
	if (start > end) [start, end] = [end, start];
	// While a bar is being dragged, conflicts follow the preview, like its arrows.
	if (drag.value && drag.value.taskName === task.name && drag.value.moved) {
		return computeDraggedRange(drag.value, start, end);
	}
	return { start, end };
}

function computeArrows() {
	const container = rowsRef.value;
	if (!container) {
		if (arrows.value.length) arrows.value = [];
		return;
	}
	const base = container.getBoundingClientRect();
	const byName = new Map(timelineTasks.value.map((t) => [t.name, t]));
	const barRect = (name) => {
		const el = container.querySelector(`[data-bar="${CSS.escape(name)}"]`);
		if (!el) return null;
		const r = el.getBoundingClientRect();
		return {
			left: r.left - base.left,
			right: r.right - base.left,
			midY: r.top - base.top + r.height / 2,
		};
	};

	const result = [];
	for (const task of timelineTasks.value) {
		for (const predName of task.depends_on || []) {
			const pred = byName.get(predName);
			if (!pred) continue;
			const from = barRect(predName);
			const to = barRect(task.name);
			if (!from || !to) continue;
			const pd = taskDates(pred);
			const td = taskDates(task);
			const conflict = !!(pd && td && td.start <= pd.end);
			const x1 = from.right;
			const y1 = from.midY;
			const x2 = to.left;
			const y2 = to.midY;
			const mid = Math.max(x1 + 10, Math.min(x2 - 10, (x1 + x2) / 2));
			const path =
				x2 >= x1 + 20
					? `M${x1},${y1} H${mid} V${y2} H${x2 - 5}`
					: `M${x1},${y1} H${x1 + 10} V${(y1 + y2) / 2} H${x2 - 10} V${y2} H${x2 - 5}`;
			result.push({
				key: `${predName}->${task.name}`,
				path,
				tipPoints: `${x2},${y2} ${x2 - 6},${y2 - 4} ${x2 - 6},${y2 + 4}`,
				conflict,
			});
		}
	}
	if (JSON.stringify(result) !== JSON.stringify(arrows.value)) arrows.value = result;
}

function scheduleArrows() {
	nextTick(computeArrows);
}

onUpdated(scheduleArrows);

onBeforeUnmount(() => {
	removeDragListeners();
	resizeObserver?.disconnect();
});

function navigatePrev() {
	const newDate = new Date(viewStartDate.value);
	newDate.setDate(newDate.getDate() - navigationStep.value);
	viewStartDate.value = newDate;
}

function navigateNext() {
	const newDate = new Date(viewStartDate.value);
	newDate.setDate(newDate.getDate() + navigationStep.value);
	viewStartDate.value = newDate;
}

function goToToday() {
	viewStartDate.value = new Date();
}

const store = useTaskStore();

function setBlocked(task, blocked) {
	store.updateTask(task.name, { is_blocked: blocked ? 1 : 0 });
}

function handleTaskClick(task) {
	if (justDragged.value) return;
	emit("task-click", task);
}

// The rows element is re-created when dated tasks reappear after an empty
// view, so observe whichever element is current.
watch(rowsRef, (element, previous) => {
	if (typeof ResizeObserver === "undefined") return;
	if (!resizeObserver) resizeObserver = new ResizeObserver(scheduleArrows);
	if (previous) resizeObserver.unobserve(previous);
	if (element) resizeObserver.observe(element);
});

onMounted(() => {
	scheduleArrows();
	// Start from beginning of current week
	const today = new Date();
	const dayOfWeek = today.getDay();
	const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Monday
	today.setDate(today.getDate() + diff);
	viewStartDate.value = today;
});
</script>

<template>
	<div class="timeline-view h-full flex flex-col bg-white text-gray-900">
		<!-- Header with navigation -->
		<div
			class="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50"
		>
			<div class="flex items-center gap-2">
				<Calendar class="w-5 h-5 text-blue-600" />
				<h3 class="text-sm font-semibold text-gray-700">{{ t("Timeline") }}</h3>
				<span class="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
					{{ timelineTasks.length }} {{ t("tasks with dates") }}
				</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="flex rounded border border-gray-300 overflow-hidden" role="group" :aria-label="t('Range')">
					<button
						v-for="days in RANGE_OPTIONS"
						:key="days"
						@click="setRange(days)"
						:aria-pressed="daysToShow === days"
						:class="[
							'px-2 py-1 text-xs font-medium',
							daysToShow === days
								? 'bg-blue-600 text-white'
								: 'text-gray-600 hover:bg-gray-200',
						]"
					>
						{{ days }}{{ t("d") }}
					</button>
				</div>
				<button
					@click="navigatePrev"
					class="p-1.5 rounded hover:bg-gray-200 text-gray-600"
					:title="t('Previous')"
				>
					<ChevronLeft class="w-4 h-4" />
				</button>
				<button
					@click="goToToday"
					class="px-3 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded"
				>
					{{ t("Today") }}
				</button>
				<button
					@click="navigateNext"
					class="p-1.5 rounded hover:bg-gray-200 text-gray-600"
					:title="t('Next')"
				>
					<ChevronRight class="w-4 h-4" />
				</button>
			</div>
		</div>

		<!-- Timeline content -->
		<div class="flex-1 overflow-auto">
			<!-- Date headers -->
			<div class="sticky top-0 z-10 bg-white border-b border-gray-200">
				<div class="flex">
					<!-- Task name column header -->
					<div class="w-64 flex-shrink-0 px-4 py-2 border-r border-gray-200 bg-gray-50">
						<span class="text-xs font-medium text-gray-500 uppercase">{{
							t("Task")
						}}</span>
					</div>
					<!-- Date columns -->
					<div class="flex-1 flex">
						<div
							v-for="header in dateHeaders"
							:key="header.date.toISOString()"
							:class="[
								'flex-1 px-1 py-2 text-center',
								isCompact ? 'min-w-3 !px-0' : 'min-w-8',
								' border-r border-gray-100',
								header.isWeekend ? 'bg-gray-100' : 'bg-white',
								header.isToday ? 'bg-blue-50' : '',
							]"
						>
							<div v-if="!isCompact" class="text-xs text-gray-500" :title="header.dayName">{{ header.dayOfWeek }}</div>
							<div
								:class="[
									isCompact ? 'text-[9px] font-medium' : 'text-sm font-medium',
									header.isToday ? 'text-blue-600' : 'text-gray-700',
								]"
							>
								{{ header.dayOfMonth }}
							</div>
							<div v-if="header.dayOfMonth === 1" class="text-xs text-gray-400">
								{{ header.month }}
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Task rows -->
			<div
				v-if="timelineTasks.length === 0"
				class="flex items-center justify-center py-12 text-gray-500"
			>
				<div class="text-center">
					<Calendar class="w-12 h-12 mx-auto mb-3 text-gray-300" />
					<p class="text-sm">{{ t("No tasks with dates to display") }}</p>
					<p class="text-xs text-gray-400 mt-1">
						{{ t("Add start or end dates to tasks") }}
					</p>
				</div>
			</div>

			<div v-else ref="rowsRef" class="relative">
				<div
					v-for="task in timelineTasks"
					:key="task.name"
					class="flex hover:bg-gray-50 border-b border-gray-100 group"
				>
					<!-- Task name -->
					<div
						class="w-64 flex-shrink-0 px-4 py-3 border-r border-gray-200 cursor-pointer"
						@click="handleTaskClick(task)"
					>
						<div class="flex items-center gap-2">
							<Diamond
								v-if="task.milestone"
								class="w-3 h-3 flex-shrink-0 text-amber-500"
							/>
							<span class="text-sm text-gray-900 truncate group-hover:text-blue-600 flex-1 min-w-0">
								{{ task.subject }}
							</span>
							<BlockedToggle
								:blocked="task.is_blocked"
								@toggle="(blocked) => setBlocked(task, blocked)"
							/>
						</div>
						<div class="flex items-center gap-2 mt-1">
							<span
								:class="[
									'text-xs px-1.5 py-0.5 rounded',
									statusColors[task.status]
										? 'text-white'
										: 'bg-gray-100 text-gray-600',
									statusColors[task.status] || '',
								]"
							>
								{{ task.status }}
							</span>
							<span v-if="task.exp_start_date" class="text-xs text-gray-400">
								{{ task.exp_start_date }}
							</span>
							<span
								v-if="task.exp_start_date && task.exp_end_date"
								class="text-xs text-gray-400"
								>→</span
							>
							<span v-if="task.exp_end_date" class="text-xs text-gray-400">
								{{ task.exp_end_date }}
							</span>
						</div>
					</div>

					<!-- Timeline bar area -->
					<div class="flex-1 relative py-2" data-timeline-area>
						<!-- Background grid -->
						<div class="absolute inset-0 flex">
							<div
								v-for="header in dateHeaders"
								:key="'bg-' + header.date.toISOString()"
								:class="[
									'flex-1 border-r border-gray-100',
									header.isWeekend ? 'bg-gray-50' : '',
									header.isToday ? 'bg-blue-50/50' : '',
								]"
							>
								<div
									v-if="header.isToday"
									class="mx-auto h-full w-0.5 bg-red-500/70"
									:title="t('Today')"
								></div>
							</div>
						</div>

						<!-- Task bar (drag to move, edges to resize) -->
						<div
							v-if="getTaskBarStyle(task)"
							:data-bar="task.name"
							:style="getTaskBarStyle(task)"
							:class="[
								'absolute top-1/2 -translate-y-1/2 h-6 rounded select-none touch-none',
								'hover:shadow-md group/bar',
								drag && drag.taskName === task.name && drag.moved
									? 'cursor-grabbing shadow-lg ring-2 ring-blue-400 z-10'
									: 'cursor-grab transition-[box-shadow]',
								statusColors[task.status] || 'bg-gray-400',
								'border-l-4',
								priorityColors[task.priority] || 'border-gray-300',
							]"
							@pointerdown="startDrag($event, task, 'move')"
							@click="handleTaskClick(task)"
							:title="`${task.subject}\n${task.exp_start_date || ''} - ${
								task.exp_end_date || ''
							}`"
						>
							<div
								class="absolute left-0 top-0 h-full w-2 cursor-ew-resize rounded-l hover:bg-white/40"
								@pointerdown="startDrag($event, task, 'resize-start')"
								@click.stop
							></div>
							<div class="px-2 py-1 text-xs text-white truncate pointer-events-none">
								{{ task.subject }}
							</div>
							<div
								class="absolute right-0 top-0 h-full w-2 cursor-ew-resize rounded-r hover:bg-white/40"
								@pointerdown="startDrag($event, task, 'resize-end')"
								@click.stop
							></div>
						</div>
					</div>
				</div>
				<!-- Dependency arrows -->
				<svg class="pointer-events-none absolute inset-0 h-full w-full overflow-visible z-20" aria-hidden="true">
					<g v-for="a in arrows" :key="a.key" :class="a.conflict ? 'text-red-500' : 'text-gray-500'">
						<path :d="a.path" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="none" />
						<polygon :points="a.tipPoints" fill="currentColor" />
					</g>
				</svg>
			</div>
		</div>
	</div>
</template>

<style scoped>
.timeline-view {
	min-height: 400px;
}
</style>
