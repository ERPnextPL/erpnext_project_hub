<template>
	<div class="min-h-screen bg-gray-50">
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="w-full px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16 gap-4">
					<div class="flex items-center gap-3 min-w-0">
						<CalendarRange class="w-6 h-6 text-violet-600 shrink-0" />
						<h1 class="text-xl font-semibold text-gray-900 whitespace-nowrap">
							{{ translate("Work Planning") }}
						</h1>
					</div>
					<div class="flex items-center gap-3 sm:gap-4 shrink-0">
						<OutlinerNav />
					</div>
				</div>
			</div>
		</header>

		<main class="w-full px-4 sm:px-6 lg:px-8 py-6 space-y-4">
			<!-- Toolbar -->
			<div
				class="flex flex-col gap-3 rounded-lg border border-gray-200 bg-white p-3 lg:flex-row lg:items-center lg:justify-between"
			>
				<div class="flex flex-wrap items-center gap-2">
					<div class="inline-flex rounded-md border border-gray-300">
						<button
							type="button"
							class="rounded-l-md px-2 py-1.5 text-gray-600 hover:bg-gray-50"
							:title="translate('Previous week')"
							:aria-label="translate('Previous week')"
							@click="store.shiftWeek(-1)"
						>
							<ChevronLeft class="h-4 w-4" />
						</button>
						<button
							type="button"
							class="border-x border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
							@click="store.goToCurrentWeek()"
						>
							{{ translate("This week") }}
						</button>
						<button
							type="button"
							class="rounded-r-md px-2 py-1.5 text-gray-600 hover:bg-gray-50"
							:title="translate('Next week')"
							:aria-label="translate('Next week')"
							@click="store.shiftWeek(1)"
						>
							<ChevronRight class="h-4 w-4" />
						</button>
					</div>
					<div class="text-sm font-semibold text-gray-900">{{ weekLabel }}</div>
					<input
						type="date"
						:value="store.weekStart"
						class="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-600 focus:border-violet-500 focus:ring-violet-500"
						:title="translate('Go to week')"
						@change="store.goToDate($event.target.value)"
					/>
				</div>

				<div class="flex flex-wrap items-center gap-2">
					<div class="relative">
						<Search class="pointer-events-none absolute left-2.5 top-2 h-4 w-4 text-gray-400" />
						<input
							v-model="store.search"
							type="text"
							:placeholder="translate('Search employee...')"
							class="w-44 rounded-md border border-gray-300 py-1.5 pl-8 pr-2 text-sm focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>
					<select
						v-if="store.canPlan && store.departments.length"
						:value="store.department"
						class="rounded-md border border-gray-300 py-1.5 pl-2 pr-8 text-sm text-gray-700 focus:border-violet-500 focus:ring-violet-500"
						@change="store.setDepartment($event.target.value)"
					>
						<option value="">{{ translate("All departments") }}</option>
						<option v-for="department in store.departments" :key="department" :value="department">
							{{ department }}
						</option>
					</select>
					<label class="flex items-center gap-1.5 text-sm text-gray-600">
						<input
							type="checkbox"
							:checked="store.showWeekend"
							class="rounded border-gray-300 text-violet-600 focus:ring-violet-500"
							@change="store.setShowWeekend($event.target.checked)"
						/>
						{{ translate("Weekend") }}
					</label>
					<button
						v-if="store.canPlan"
						type="button"
						class="inline-flex items-center gap-1.5 rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
						:disabled="copying || store.loading"
						:title="translate('Copy the previous week\'s plan into this week')"
						@click="copyPreviousWeek"
					>
						<Copy class="h-4 w-4" />
						{{ translate("Copy previous week") }}
					</button>
					<button
						type="button"
						class="rounded-md border border-gray-300 p-1.5 text-gray-600 hover:bg-gray-50"
						:title="translate('Refresh')"
						:aria-label="translate('Refresh')"
						@click="store.fetchPlan()"
					>
						<RefreshCw class="h-4 w-4" :class="{ 'animate-spin': store.loading }" />
					</button>
				</div>
			</div>

			<div
				v-if="store.loaded && !store.canPlan"
				class="flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800"
			>
				<Info class="mt-0.5 h-4 w-4 shrink-0" />
				{{ translate("This is your work plan. Project managers plan the work of the team.") }}
			</div>

			<!-- Summary -->
			<div v-if="store.loaded" class="grid grid-cols-2 gap-3 lg:grid-cols-4">
				<div class="rounded-lg border border-gray-200 bg-white px-4 py-3">
					<div class="text-xs font-medium uppercase tracking-wide text-gray-500">
						{{ translate("Available hours") }}
					</div>
					<div class="mt-1 text-2xl font-semibold text-gray-900 tabular-nums">
						{{ formatHours(store.weekTotals.available) }} h
					</div>
				</div>
				<div class="rounded-lg border border-gray-200 bg-white px-4 py-3">
					<div class="text-xs font-medium uppercase tracking-wide text-gray-500">
						{{ translate("Planned hours") }}
					</div>
					<div class="mt-1 flex items-baseline gap-2">
						<span class="text-2xl font-semibold text-gray-900 tabular-nums">
							{{ formatHours(store.weekTotals.planned) }} h
						</span>
						<span v-if="store.weekTotals.available > 0" class="text-sm text-gray-500 tabular-nums">
							{{ utilization }}%
						</span>
					</div>
				</div>
				<div class="rounded-lg border border-gray-200 bg-white px-4 py-3">
					<div class="text-xs font-medium uppercase tracking-wide text-gray-500">
						{{ translate("Free hours") }}
					</div>
					<div class="mt-1 text-2xl font-semibold text-green-700 tabular-nums">
						{{ formatHours(store.weekTotals.free) }} h
					</div>
				</div>
				<div class="rounded-lg border border-gray-200 bg-white px-4 py-3">
					<div class="text-xs font-medium uppercase tracking-wide text-gray-500">
						{{ translate("Overbooked days") }}
					</div>
					<div
						class="mt-1 text-2xl font-semibold tabular-nums"
						:class="store.weekTotals.overbookedDays ? 'text-red-600' : 'text-gray-900'"
					>
						{{ store.weekTotals.overbookedDays }}
					</div>
				</div>
			</div>

			<!-- Grid -->
			<div v-if="!store.loaded && store.loading" class="space-y-2">
				<div
					v-for="i in 4"
					:key="i"
					class="h-24 animate-pulse rounded-lg border border-gray-200 bg-white"
				></div>
			</div>
			<div
				v-else-if="store.error && !store.loaded"
				class="rounded-lg border border-red-200 bg-white py-12 text-center"
			>
				<AlertCircle class="mx-auto mb-4 h-12 w-12 text-red-400" />
				<h3 class="mb-2 text-lg font-medium text-gray-900">
					{{ translate("Failed to load the work plan") }}
				</h3>
				<p class="mb-4 text-gray-500">{{ store.error }}</p>
				<button
					type="button"
					class="rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700"
					@click="store.fetchPlan()"
				>
					{{ translate("Try again") }}
				</button>
			</div>
			<div
				v-else-if="store.loaded && !store.filteredEmployees.length"
				class="rounded-lg border border-gray-200 bg-white py-12 text-center text-gray-500"
			>
				<Users class="mx-auto mb-3 h-10 w-10 text-gray-300" />
				{{
					store.employees.length
						? translate("No employees match the search")
						: store.canPlan
						? translate("No active employees")
						: translate("Your user is not linked to an active employee")
				}}
			</div>
			<WorkPlanGrid
				v-else-if="store.loaded"
				:class="{ 'opacity-60 pointer-events-none': store.loading }"
				@add="openAdd"
				@edit="openEdit"
			/>

			<div
				v-if="store.loaded && store.filteredEmployees.length"
				class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500"
			>
				<span class="flex items-center gap-1.5">
					<span class="h-2 w-4 rounded-full bg-blue-400"></span>{{ translate("Free time left") }}
				</span>
				<span class="flex items-center gap-1.5">
					<span class="h-2 w-4 rounded-full bg-green-500"></span>{{ translate("Fully planned") }}
				</span>
				<span class="flex items-center gap-1.5">
					<span class="h-2 w-4 rounded-full bg-red-500"></span>{{ translate("Overbooked") }}
				</span>
				<span>{{ translate("Availability comes from shifts, holiday lists and approved leave; without them a working day has {0} h.", [formatHours(store.defaultDailyHours)]) }}</span>
			</div>

			<!-- Projects this week -->
			<div
				v-if="store.loaded && store.projectSummary.length"
				class="rounded-lg border border-gray-200 bg-white"
			>
				<div class="border-b border-gray-200 px-4 py-3">
					<h2 class="text-sm font-semibold text-gray-900">
						{{ translate("Projects this week") }}
					</h2>
				</div>
				<div class="divide-y divide-gray-100">
					<div
						v-for="project in store.projectSummary"
						:key="project.project"
						class="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center"
					>
						<div class="flex min-w-0 items-center gap-2 sm:w-72 sm:shrink-0">
							<span
								class="h-2.5 w-2.5 shrink-0 rounded-full"
								:class="getProjectColor(project.project).dot"
							></span>
							<router-link
								:to="`/project-hub/${encodeURIComponent(project.project)}`"
								class="truncate text-sm font-medium text-gray-900 hover:text-violet-700 hover:underline"
							>
								{{ project.project_name }}
							</router-link>
							<span class="ml-auto shrink-0 text-sm font-semibold text-gray-900 tabular-nums">
								{{ formatHours(project.hours) }} h
							</span>
						</div>
						<div class="flex flex-wrap gap-1.5">
							<span
								v-for="person in project.employees"
								:key="person.employee"
								class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
							>
								{{ person.employee_name }}
								<span class="font-semibold tabular-nums">{{ formatHours(person.hours) }} h</span>
							</span>
						</div>
					</div>
				</div>
			</div>
		</main>

		<WorkPlanEntryModal
			:show="modal.show"
			:employee="modal.employee"
			:date="modal.date"
			:entry="modal.entry"
			@close="modal.show = false"
		/>

		<BackToDeskButton />
	</div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
	AlertCircle,
	CalendarRange,
	ChevronLeft,
	ChevronRight,
	Copy,
	Info,
	RefreshCw,
	Search,
	Users,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import BackToDeskButton from "../components/BackToDeskButton.vue";
import WorkPlanGrid from "../components/work-planning/WorkPlanGrid.vue";
import WorkPlanEntryModal from "../components/work-planning/WorkPlanEntryModal.vue";
import {
	useWorkPlanningStore,
	formatDay,
	formatHours,
} from "../stores/workPlanningStore";
import { getProjectColor } from "../utils/projectColors";
import { translate } from "../utils/translation";

const store = useWorkPlanningStore();

const copying = ref(false);
const modal = reactive({ show: false, employee: null, date: null, entry: null });

const weekLabel = computed(() => {
	if (!store.dates.length) return "";
	const first = store.dates[0];
	const last = store.dates[store.dates.length - 1];
	const range = `${formatDay(first, { day: "numeric", month: "short" })} – ${formatDay(last, {
		day: "numeric",
		month: "short",
		year: "numeric",
	})}`;
	return `${range} · ${translate("week {0}", [getISOWeek(first)])}`;
});

const utilization = computed(() =>
	Math.round((store.weekTotals.planned / store.weekTotals.available) * 100)
);

function getISOWeek(isoDate) {
	const [year, month, day] = isoDate.split("-").map(Number);
	const date = new Date(Date.UTC(year, month - 1, day));
	// The ISO week is the one containing that week's Thursday.
	date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7));
	const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
	return Math.ceil(((date - yearStart) / 86400000 + 1) / 7);
}

function openAdd({ employee, date }) {
	Object.assign(modal, { show: true, employee, date, entry: null });
}

function openEdit({ employee, date, entry }) {
	Object.assign(modal, { show: true, employee, date, entry });
}

async function copyPreviousWeek() {
	if (!window.confirm(translate("Copy the previous week's plan into this week?"))) return;
	copying.value = true;
	try {
		await store.copyPreviousWeek();
	} catch (err) {
		// apiCall already showed the error
	} finally {
		copying.value = false;
	}
}

onMounted(() => {
	store.fetchPlan();
});
</script>
