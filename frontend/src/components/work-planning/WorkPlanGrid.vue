<template>
	<div class="bg-white border border-gray-200 rounded-lg overflow-x-auto">
		<table class="min-w-full border-separate border-spacing-0 text-sm">
			<thead>
				<tr>
					<th
						class="sticky left-0 z-10 bg-gray-50 border-b border-gray-200 px-3 sm:px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 w-36 min-w-[9rem] sm:w-56 sm:min-w-[13rem]"
					>
						{{ translate("Employee") }}
					</th>
					<th
						v-for="date in store.visibleDates"
						:key="date"
						class="border-b border-l border-gray-200 px-2 py-2 text-left font-normal min-w-[9.5rem]"
						:class="date === today ? 'bg-violet-50' : 'bg-gray-50'"
					>
						<div
							class="text-xs font-semibold uppercase tracking-wide"
							:class="date === today ? 'text-violet-700' : 'text-gray-600'"
						>
							{{ formatDay(date) }}
						</div>
						<div class="mt-0.5 text-xs text-gray-500 tabular-nums">
							{{ formatHours(store.getDayTotals(date).planned) }} /
							{{ formatHours(store.getDayTotals(date).available) }} h
						</div>
					</th>
					<th
						class="border-b border-l border-gray-200 bg-gray-50 px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 min-w-[8.5rem]"
					>
						{{ translate("Week total") }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="employee in store.filteredEmployees" :key="employee.name">
					<td
						class="sticky left-0 z-10 bg-white border-b border-gray-100 px-3 sm:px-4 py-3 align-top"
					>
						<div class="flex items-center gap-3 min-w-0">
							<div
								class="hidden h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-violet-100 text-xs font-semibold text-violet-700 sm:flex"
							>
								<img
									v-if="employee.image"
									:src="employee.image"
									:alt="employee.employee_name"
									class="h-full w-full object-cover"
								/>
								<span v-else>{{ initials(employee.employee_name) }}</span>
							</div>
							<div class="min-w-0">
								<div class="truncate font-medium text-gray-900" :title="employee.name">
									{{ employee.employee_name }}
								</div>
								<div
									v-if="employee.designation || employee.department"
									class="truncate text-xs text-gray-500"
								>
									{{ employee.designation || employee.department }}
								</div>
							</div>
						</div>
					</td>

					<td
						v-for="date in store.visibleDates"
						:key="date"
						class="border-b border-l border-gray-100 p-1.5 align-top"
					>
						<div
							class="group relative flex h-full min-h-[5.5rem] flex-col gap-1 rounded-md border p-1.5"
							:class="cellClass(employee.name, date)"
						>
							<div class="flex items-center justify-between gap-1 text-xs">
								<span
									class="font-medium tabular-nums"
									:class="LOAD_TEXT[load(employee.name, date)]"
									:title="translate('Planned / available hours')"
								>
									<AlertTriangle
										v-if="load(employee.name, date) === 'over'"
										class="inline h-3 w-3 -mt-0.5"
									/>
									{{ formatHours(store.getPlanned(employee.name, date)) }} /
									{{ formatHours(store.getAvailable(employee.name, date)) }} h
								</span>
								<button
									v-if="
										store.canPlan &&
										(store.getEntries(employee.name, date).length ||
											store.getAvailable(employee.name, date) <= 0)
									"
									type="button"
									class="rounded p-0.5 text-gray-400 opacity-0 transition hover:bg-white hover:text-violet-600 focus:opacity-100 group-hover:opacity-100"
									:title="translate('Plan work')"
									:aria-label="translate('Plan work')"
									@click="emit('add', { employee, date })"
								>
									<Plus class="h-4 w-4" />
								</button>
							</div>

							<div
								v-if="dayLabel(employee.name, date)"
								class="flex items-center gap-1 text-[11px] leading-tight text-gray-500"
								:title="dayLabel(employee.name, date)"
							>
								<Palmtree
									v-if="store.getDay(employee.name, date).status === 'leave'"
									class="h-3 w-3 shrink-0 text-amber-500"
								/>
								<span class="truncate">{{ dayLabel(employee.name, date) }}</span>
							</div>

							<button
								v-for="entry in store.getEntries(employee.name, date)"
								:key="entry.name"
								type="button"
								class="flex w-full items-center justify-between gap-1 rounded border px-1.5 py-1 text-left text-xs transition"
								:class="[
									getProjectColor(entry.project).chip,
									store.canPlan ? 'cursor-pointer' : 'cursor-default',
								]"
								:title="entryTitle(entry)"
								@click="store.canPlan && emit('edit', { employee, date, entry })"
							>
								<span class="truncate">{{ entry.project_name || entry.project }}</span>
								<span class="shrink-0 font-semibold tabular-nums">
									{{ formatHours(entry.hours) }} h
								</span>
							</button>

							<button
								v-if="
									store.canPlan &&
									!store.getEntries(employee.name, date).length &&
									store.getAvailable(employee.name, date) > 0
								"
								type="button"
								class="flex flex-1 items-center justify-center rounded border border-dashed border-gray-200 text-xs text-gray-400 transition hover:border-violet-300 hover:bg-violet-50 hover:text-violet-600"
								@click="emit('add', { employee, date })"
							>
								<Plus class="mr-1 h-3.5 w-3.5" />
								{{ translate("Plan hours") }}
							</button>

							<div
								v-if="store.getAvailable(employee.name, date) > 0"
								class="mt-auto h-1 w-full overflow-hidden rounded-full bg-gray-100"
							>
								<div
									class="h-full rounded-full"
									:class="LOAD_BAR[load(employee.name, date)]"
									:style="{ width: barWidth(store.getPlanned(employee.name, date), store.getAvailable(employee.name, date)) }"
								></div>
							</div>
						</div>
					</td>

					<td class="border-b border-l border-gray-100 px-3 py-3 align-top">
						<div
							class="text-sm font-semibold tabular-nums"
							:class="LOAD_TEXT[weekLoad(employee.name)]"
						>
							{{ formatHours(store.getEmployeeWeek(employee.name).planned) }} /
							{{ formatHours(store.getEmployeeWeek(employee.name).available) }} h
						</div>
						<div class="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
							<div
								class="h-full rounded-full"
								:class="LOAD_BAR[weekLoad(employee.name)]"
								:style="{ width: barWidth(store.getEmployeeWeek(employee.name).planned, store.getEmployeeWeek(employee.name).available) }"
							></div>
						</div>
						<div class="mt-1 text-xs text-gray-500">
							{{ weekHint(employee.name) }}
						</div>
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { AlertTriangle, Palmtree, Plus } from "lucide-vue-next";
import {
	useWorkPlanningStore,
	formatDay,
	formatHours,
	getLoadState,
	roundHours,
	toISODate,
} from "../../stores/workPlanningStore";
import { getProjectColor } from "../../utils/projectColors";
import { translate } from "../../utils/translation";

const emit = defineEmits(["add", "edit"]);

const store = useWorkPlanningStore();
const today = toISODate(new Date());

const LOAD_TEXT = {
	empty: "text-gray-500",
	partial: "text-blue-700",
	full: "text-green-700",
	over: "text-red-600",
};

const LOAD_BAR = {
	empty: "bg-gray-200",
	partial: "bg-blue-400",
	full: "bg-green-500",
	over: "bg-red-500",
};

const DAY_STATUS_LABELS = {
	weekend: "Day off",
	holiday: "Holiday",
	leave: "Leave",
	inactive: "Not employed",
};

function load(employee, date) {
	return getLoadState(store.getPlanned(employee, date), store.getAvailable(employee, date));
}

function weekLoad(employee) {
	const week = store.getEmployeeWeek(employee);
	return getLoadState(week.planned, week.available);
}

function cellClass(employee, date) {
	const day = store.getDay(employee, date);
	if (load(employee, date) === "over") return "border-red-200 bg-red-50/60";
	if (day.hours <= 0) return "border-transparent bg-gray-100/70";
	if (day.status === "leave" || day.status === "holiday") return "border-amber-100 bg-amber-50/50";
	return "border-transparent bg-white";
}

function dayLabel(employee, date) {
	const day = store.getDay(employee, date);
	if (day.status === "work") return "";

	const label = translate(DAY_STATUS_LABELS[day.status] || day.status);
	const text = day.reason ? `${label}: ${day.reason}` : label;
	return day.half_day ? `½ ${text}` : text;
}

function barWidth(planned, available) {
	if (available <= 0) return planned > 0 ? "100%" : "0%";
	return `${Math.min(planned / available, 1) * 100}%`;
}

function weekHint(employee) {
	const week = store.getEmployeeWeek(employee);
	const difference = roundHours(week.available - week.planned);
	if (difference < 0) return translate("{0} h over", [formatHours(-difference)]);
	if (week.available <= 0) return translate("Not available");
	return translate("{0} h free", [formatHours(difference)]);
}

function entryTitle(entry) {
	return [entry.project_name || entry.project, entry.project, entry.note]
		.filter(Boolean)
		.filter((value, index, values) => values.indexOf(value) === index)
		.join("\n");
}

function initials(name) {
	return (name || "?")
		.split(/\s+/)
		.filter(Boolean)
		.slice(0, 2)
		.map((word) => word[0].toUpperCase())
		.join("");
}
</script>
