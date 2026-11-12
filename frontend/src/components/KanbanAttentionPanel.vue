<script setup>
import { computed, ref, watch } from "vue";
import { ChevronRight, ChevronLeft, AlertTriangle } from "lucide-vue-next";
import { translate } from "../utils/translation";
import { getStatusLabel } from "../utils/taskStatus";

const props = defineProps({
	tasks: { type: Array, required: true },
	highlightedTask: { type: String, default: null },
	// Section keys to leave out (e.g. "unassigned" where every task is mine)
	exclude: { type: Array, default: () => [] },
});
const emit = defineEmits(["focus-task"]);

const STORAGE_KEY = "projectHub.kanban.attentionCollapsed";
function loadCollapsed() {
	try {
		return localStorage.getItem(STORAGE_KEY) === "1";
	} catch {
		return false;
	}
}
const collapsed = ref(loadCollapsed());
watch(collapsed, (value) => {
	try {
		localStorage.setItem(STORAGE_KEY, value ? "1" : "0");
	} catch {
		/* storage unavailable */
	}
});

const CLOSED = ["Completed", "Cancelled", "Closed", "Template"];

function hasAssignee(task) {
	try {
		const list = JSON.parse(task._assign || "[]");
		return Array.isArray(list) && list.length > 0;
	} catch {
		return false;
	}
}

const sections = computed(() => {
	const open = props.tasks.filter((t) => !CLOSED.includes(t.status));
	const defs = [
		{
			key: "overdue",
			label: translate("Overdue"),
			badge: "bg-red-100 text-red-700",
			tasks: open.filter((t) => t.is_overdue),
		},
		{
			key: "blocked",
			label: translate("Blocked"),
			badge: "bg-amber-100 text-amber-800",
			tasks: open.filter((t) => t.is_blocked),
		},
		{
			key: "unassigned",
			label: translate("Unassigned"),
			badge: "bg-gray-200 text-gray-700",
			tasks: open.filter((t) => !hasAssignee(t)),
		},
		{
			key: "review",
			label: getStatusLabel("Pending Review"),
			badge: "bg-purple-100 text-purple-700",
			tasks: open.filter((t) => t.status === "Pending Review"),
		},
	];
	return defs.filter((section) => !props.exclude.includes(section.key) && section.tasks.length > 0);
});

const total = computed(() => {
	const names = new Set();
	sections.value.forEach((s) => s.tasks.forEach((t) => names.add(t.name)));
	return names.size;
});
</script>

<template>
	<!-- Collapsed: a narrow strip on the right edge -->
	<aside
		v-if="collapsed"
		class="flex w-10 flex-shrink-0 flex-col items-center gap-3 border-l border-gray-200 bg-white py-3"
		:aria-label="translate('Needs attention')"
	>
		<button
			type="button"
			class="rounded-lg border border-gray-300 p-1 text-gray-500 hover:bg-gray-50"
			:title="translate('Expand panel')"
			:aria-label="translate('Expand panel')"
			:aria-expanded="false"
			@click="collapsed = false"
		>
			<ChevronLeft class="h-4 w-4" />
		</button>
		<span
			v-if="total > 0"
			class="rounded-full bg-amber-100 px-1.5 text-xs font-semibold leading-5 text-amber-800"
			:title="translate('Needs attention')"
		>
			{{ total }}
		</span>
		<AlertTriangle v-else class="h-4 w-4 text-gray-300" aria-hidden="true" />
		<span class="mt-1 text-xs font-medium text-gray-500 [writing-mode:vertical-rl]">
			{{ translate("Needs attention") }}
		</span>
	</aside>

	<!-- Expanded -->
	<aside
		v-else
		class="flex w-80 flex-shrink-0 flex-col overflow-y-auto border-l border-gray-200 bg-white"
		:aria-label="translate('Needs attention')"
	>
		<div class="flex items-center gap-2 border-b border-gray-200 px-4 py-3">
			<strong class="flex-1 text-sm font-semibold text-gray-900">{{ translate("Needs attention") }}</strong>
			<button
				type="button"
				class="rounded-lg border border-gray-300 p-1 text-gray-500 hover:bg-gray-50"
				:title="translate('Collapse panel')"
				:aria-label="translate('Collapse panel')"
				:aria-expanded="true"
				@click="collapsed = true"
			>
				<ChevronRight class="h-4 w-4" />
			</button>
		</div>

		<p v-if="sections.length === 0" class="px-4 py-6 text-center text-sm text-gray-500">
			{{ translate("Nothing needs attention") }}
		</p>

		<section v-for="section in sections" :key="section.key" class="border-b border-gray-100 px-3 py-3">
			<h3 class="mb-1 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
				{{ section.label }}
				<span class="rounded-full px-2 text-[11px] leading-[18px]" :class="section.badge">
					{{ section.tasks.length }}
				</span>
			</h3>
			<button
				v-for="task in section.tasks"
				:key="task.name"
				type="button"
				class="block w-full rounded-lg px-2 py-1.5 text-left text-sm text-gray-900 hover:bg-gray-100"
				:class="highlightedTask === task.name ? 'bg-amber-50 ring-1 ring-amber-300' : ''"
				@click="emit('focus-task', task.name)"
			>
				<span class="block truncate">{{ task.subject }}</span>
				<span class="block text-[11px] text-gray-500">
					{{ getStatusLabel(task.status) }}<template v-if="task.exp_end_date"> · {{ String(task.exp_end_date).slice(0, 10) }}</template>
				</span>
			</button>
		</section>
	</aside>
</template>
