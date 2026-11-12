<template>
	<div class="space-y-4">
		<div v-if="loading" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
			<div v-for="item in 5" :key="item" class="h-24 animate-pulse rounded-lg border border-gray-200 bg-white"></div>
		</div>
		<div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 px-4 py-6 text-center text-sm text-red-700">{{ error }}</div>
		<template v-else-if="forecast">
			<div class="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">{{ translate("Planned hours come from Work Plan Entry. Demand is the remaining estimated effort of active tasks in the selected period. They are shown separately to avoid double counting.") }}</div>

			<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
				<div v-for="card in summaryCards" :key="card.label" class="rounded-lg border border-gray-200 bg-white px-4 py-3">
					<div class="text-xs font-medium uppercase tracking-wide text-gray-500">{{ card.label }}</div>
					<div class="mt-1 text-2xl font-semibold tabular-nums" :class="card.color">{{ formatHours(card.value) }} {{ card.unit }}</div>
					<div class="mt-1 text-xs text-gray-500">{{ card.note }}</div>
				</div>
			</div>

			<div class="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(20rem,1fr)]">
				<section class="overflow-hidden rounded-lg border border-gray-200 bg-white">
					<div class="flex items-center justify-between border-b border-gray-200 px-4 py-3"><div><h2 class="text-sm font-semibold text-gray-900">{{ translate("Employee capacity") }}</h2><p class="mt-0.5 text-xs text-gray-500">{{ rangeLabel }}</p></div><div class="hidden gap-3 text-xs text-gray-500 sm:flex"><span><i class="mr-1 inline-block h-2 w-2 rounded-full bg-blue-500"></i>{{ translate("Planned") }}</span><span><i class="mr-1 inline-block h-2 w-2 rounded-full bg-amber-400"></i>{{ translate("Demand") }}</span></div></div>
					<div class="overflow-x-auto"><table class="min-w-full text-sm"><thead class="bg-gray-50 text-xs uppercase tracking-wide text-gray-500"><tr><th class="px-4 py-3 text-left">{{ translate("Employee") }}</th><th class="px-3 py-3 text-right">{{ translate("Capacity") }}</th><th class="px-3 py-3 text-right">{{ translate("Planned") }}</th><th class="px-3 py-3 text-right">{{ translate("Demand") }}</th><th class="px-3 py-3 text-right">{{ translate("Gap") }}</th><th class="px-4 py-3 text-right">{{ translate("Load") }}</th></tr></thead><tbody class="divide-y divide-gray-100">
						<template v-for="employee in forecast.employees" :key="employee.employee">
							<tr class="transition hover:bg-gray-50" :class="employee.uncovered_hours > 0 ? 'bg-amber-50/30' : ''"><td class="whitespace-nowrap px-4 py-3"><div class="font-medium text-gray-900">{{ employee.employee_name }}</div><div class="text-xs text-gray-500">{{ employee.tasks.length }} {{ translate("active tasks") }}</div></td><td class="px-3 py-3 text-right tabular-nums text-gray-600">{{ formatHours(employee.available_hours) }} h</td><td class="px-3 py-3 text-right tabular-nums text-blue-700">{{ formatHours(employee.planned_hours) }} h</td><td class="px-3 py-3 text-right tabular-nums text-amber-700">{{ formatHours(employee.demand_hours) }} h</td><td class="px-3 py-3 text-right tabular-nums" :class="employee.uncovered_hours > 0 ? 'font-semibold text-red-600' : 'text-green-700'">{{ employee.uncovered_hours > 0 ? `-${formatHours(employee.uncovered_hours)}` : formatHours(employee.free_hours) }} h</td><td class="px-4 py-3 text-right"><div class="font-medium tabular-nums" :class="loadClass(employee.forecast_utilization)">{{ Math.round(employee.forecast_utilization) }}%</div><div class="mt-1 ml-auto h-1.5 w-20 overflow-hidden rounded-full bg-gray-100"><div class="h-full rounded-full" :class="loadBarClass(employee.forecast_utilization)" :style="{ width: `${Math.min(employee.forecast_utilization, 100)}%` }"></div></div><button v-if="employee.tasks.length" type="button" class="mt-1 text-xs text-violet-600 hover:underline" @click="toggle(employee.employee)">{{ expanded[employee.employee] ? translate("Hide tasks") : translate("Show tasks") }}</button></td></tr>
							<tr v-if="expanded[employee.employee]" :key="`${employee.employee}-tasks`" class="bg-gray-50"><td colspan="6" class="px-4 py-3"><div class="grid gap-2 md:grid-cols-2"><button v-for="task in employee.tasks" :key="task.name" type="button" class="rounded-md border border-gray-200 bg-white p-3 text-left transition hover:border-violet-300 hover:bg-violet-50" @click="openTask(task.name, task.project)"><div class="flex items-start justify-between gap-2"><span class="min-w-0 truncate text-sm font-medium text-gray-800">{{ task.subject }}</span><span class="shrink-0 text-xs font-semibold" :class="task.status === 'Working' ? 'text-blue-700' : 'text-amber-700'">{{ translate(task.status) }}</span></div><div class="mt-1 flex items-center justify-between gap-2 text-xs text-gray-500"><span class="truncate">{{ task.project_name }}</span><span class="shrink-0 tabular-nums">{{ formatHours(task.remaining_hours) }} h {{ translate("remaining") }}</span></div><div class="mt-2 flex items-center justify-between text-xs"><span :class="task.is_undated ? 'text-orange-600' : 'text-gray-500'">{{ task.is_undated ? translate("No dates") : formatDue(task.due_date) }}</span><span class="tabular-nums text-gray-500">{{ Math.round(task.progress || 0) }}%</span></div></button></div></td></tr>
						</template></tbody></table></div>
				</section>

				<section class="rounded-lg border border-gray-200 bg-white"><div class="border-b border-gray-200 px-4 py-3"><h2 class="text-sm font-semibold text-gray-900">{{ translate("Project demand") }}</h2><p class="mt-0.5 text-xs text-gray-500">{{ translate("Planned hours vs estimated demand") }}</p></div><div v-if="!forecast.projects.length" class="px-4 py-10 text-center text-sm text-gray-500">{{ translate("No project demand found for this period") }}</div><div v-else class="divide-y divide-gray-100"><div v-for="project in forecast.projects" :key="project.project" class="px-4 py-3"><div class="flex items-center justify-between gap-3"><span class="min-w-0 truncate text-sm font-medium text-gray-800">{{ project.project_name }}</span><span class="shrink-0 text-xs text-gray-500">{{ project.employees }} {{ translate("people") }}</span></div><div class="mt-2 flex items-center gap-2 text-xs"><span class="w-16 text-gray-500">{{ translate("Plan") }}</span><div class="h-2 flex-1 overflow-hidden rounded-full bg-gray-100"><div class="h-full rounded-full bg-blue-500" :style="{ width: projectBar(project.planned_hours, project.demand_hours) }"></div></div><span class="w-14 text-right tabular-nums text-blue-700">{{ formatHours(project.planned_hours) }} h</span></div><div class="mt-1 flex items-center gap-2 text-xs"><span class="w-16 text-gray-500">{{ translate("Demand") }}</span><div class="h-2 flex-1 overflow-hidden rounded-full bg-gray-100"><div class="h-full rounded-full bg-amber-400" :style="{ width: projectBar(project.demand_hours, project.demand_hours) }"></div></div><span class="w-14 text-right tabular-nums text-amber-700">{{ formatHours(project.demand_hours) }} h</span></div><div v-if="project.uncovered_hours > 0" class="mt-2 text-xs font-medium text-red-600">{{ translate("Uncovered") }}: {{ formatHours(project.uncovered_hours) }} h</div></div></div><div v-if="forecast.summary.undated_backlog_hours" class="border-t border-amber-100 bg-amber-50 px-4 py-3 text-xs text-amber-800">{{ translate("Undated task backlog") }}: <strong>{{ formatHours(forecast.summary.undated_backlog_hours) }} h</strong>. {{ translate("Add task dates to include this work in a period forecast.") }}</div></section>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed, reactive } from "vue";
import { useRouter } from "vue-router";
import { translate } from "../../utils/translation";
import { formatHours } from "../../stores/workPlanningStore";

const props = defineProps({ forecast: { type: Object, default: null }, loading: { type: Boolean, default: false }, error: { type: String, default: "" } });
const expanded = reactive({});
const router = useRouter();
const rangeLabel = computed(() => {
	if (!props.forecast) return "";
	const format = (value) => new Intl.DateTimeFormat(undefined, { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T12:00:00`));
	return `${format(props.forecast.start_date)} – ${format(props.forecast.end_date)}`;
});
const summaryCards = computed(() => {
	if (!props.forecast) return [];
	const summary = props.forecast.summary;
	return [
		{ label: translate("Available capacity"), value: summary.available_hours, unit: "h", color: "text-gray-900", note: translate("from shifts, leave and holidays") },
		{ label: translate("Planned work"), value: summary.planned_hours, unit: "h", color: "text-blue-700", note: `${Math.round(summary.utilization)}% ${translate("capacity used")}` },
		{ label: translate("Estimated demand"), value: summary.demand_hours, unit: "h", color: "text-amber-700", note: `${Math.round(summary.forecast_utilization)}% ${translate("forecast load")}` },
		{ label: translate("Uncovered work"), value: summary.uncovered_hours, unit: "h", color: summary.uncovered_hours > 0 ? "text-red-600" : "text-green-700", note: translate("demand minus planned") },
		{ label: translate("Free capacity"), value: summary.free_hours, unit: "h", color: "text-green-700", note: translate("after planned work") },
	];
});
function toggle(employee) { expanded[employee] = !expanded[employee]; }
function projectBar(value, total) { return total ? `${Math.min((value / total) * 100, 100)}%` : "0%"; }
function loadClass(value) { if (value > 100) return "text-red-600"; if (value >= 85) return "text-amber-700"; return "text-green-700"; }
function loadBarClass(value) { if (value > 100) return "bg-red-500"; if (value >= 85) return "bg-amber-400"; return "bg-green-500"; }
function formatDue(value) { return value ? new Intl.DateTimeFormat(undefined, { day: "2-digit", month: "short" }).format(new Date(`${String(value).slice(0, 10)}T12:00:00`)) : translate("No date"); }
function openTask(name, project) { if (project) { router.push({ name: "ProjectOutliner", params: { projectId: project, taskId: name } }); return; } window.open(`/app/task/${encodeURIComponent(name)}`, "_blank"); }
</script>
