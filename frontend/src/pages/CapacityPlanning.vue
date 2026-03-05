<script setup>
import { onMounted, watch } from "vue";
import {
	LayoutGrid,
	ChevronLeft,
	ChevronRight,
	Plus,
	Pencil,
	Trash2,
	AlertTriangle,
	Clock,
	X,
	Loader2,
	RefreshCw,
	CalendarDays,
	Users,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import BackToDeskButton from "../components/BackToDeskButton.vue";
import { translate } from "../utils/translation";
import {
	useCapacityPlanningStore,
	formatDayHeader,
} from "../stores/capacityPlanningStore";

const store = useCapacityPlanningStore();

const userLocale = () => window?.frappe?.boot?.lang || navigator?.language || "pl-PL";

onMounted(async () => {
	await store.fetchProjects();
	await store.fetchData();
});

watch(
	() => [store.weekStart, store.projectFilter, store.employeeFilter],
	() => store.fetchData(),
	{ flush: "post" }
);

// ── Helpers ───────────────────────────────────────────────────────────────

function dayLabel(iso) {
	return formatDayHeader(iso, userLocale());
}

function freeHoursClass(free, capacity) {
	const r = free / capacity;
	if (r <= 0) return "bg-red-100 text-red-700 border-red-200";
	if (r < 0.5) return "bg-amber-100 text-amber-700 border-amber-200";
	return "bg-emerald-100 text-emerald-700 border-emerald-200";
}

function cellClass(dayData) {
	if (dayData.overloaded) return "border-red-300 bg-red-50";
	if (dayData.allocations.length === 0) return "border-dashed border-gray-200 bg-gray-50/40";
	return "border-blue-100 bg-white";
}

function weeklyUtilClass(emp) {
	const r = emp.weekly_planned_hours / emp.weekly_capacity_hours;
	if (r > 1) return "text-red-600 font-bold";
	if (r >= 0.9) return "text-amber-600 font-semibold";
	return "text-gray-700";
}

function hoursBarWidth(emp) {
	const r = Math.min(emp.weekly_planned_hours / emp.weekly_capacity_hours, 1);
	return `${Math.round(r * 100)}%`;
}

function hoursBarColor(emp) {
	const r = emp.weekly_planned_hours / emp.weekly_capacity_hours;
	if (r > 1) return "bg-red-500";
	if (r >= 0.9) return "bg-amber-400";
	return "bg-blue-500";
}

function openEdit(alloc, emp, day) {
	store.openEditModal({
		allocation: { ...alloc, day },
		employee: emp.employee,
		employeeFullName: emp.full_name,
	});
}
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<!-- ─── Header ─────────────────────────────────────────────────── -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="w-full px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16 gap-3 flex-wrap">
					<!-- Title -->
					<div class="flex items-center gap-2 shrink-0">
						<LayoutGrid class="w-5 h-5 text-purple-600" />
						<h1 class="text-lg font-semibold text-gray-900 hidden sm:block">
							{{ translate("Capacity Planning") }}
						</h1>
					</div>

					<!-- ── Controls ─────────────────────────────────────── -->
					<div class="flex items-center gap-2 flex-wrap flex-1 justify-center">

						<!-- Week navigator -->
						<div class="flex items-center bg-gray-100 rounded-lg overflow-hidden">
							<button
								class="px-2 py-1.5 hover:bg-white transition-colors"
								:title="translate('Previous week')"
								@click="store.prevWeek()"
							>
								<ChevronLeft class="w-4 h-4 text-gray-600" />
							</button>
							<button
								class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-white transition-colors whitespace-nowrap min-w-[148px] text-center"
								:title="translate('Go to current week')"
								@click="store.goToCurrentWeek()"
							>
								{{ store.weekLabel }}
							</button>
							<button
								class="px-2 py-1.5 hover:bg-white transition-colors"
								:title="translate('Next week')"
								@click="store.nextWeek()"
							>
								<ChevronRight class="w-4 h-4 text-gray-600" />
							</button>
						</div>

						<!-- Project filter -->
						<div class="flex items-center gap-1.5">
							<CalendarDays class="w-4 h-4 text-gray-400 shrink-0" />
							<select
								:value="store.projectFilter"
								class="text-sm border border-gray-200 rounded-md px-2.5 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-400 min-w-[160px]"
								@change="store.setProject($event.target.value)"
							>
								<option value="">{{ translate("All projects") }}</option>
								<option
									v-for="p in store.projects"
									:key="p.name"
									:value="p.name"
								>
									{{ p.project_name || p.name }}
								</option>
							</select>
						</div>

						<!-- Employee filter -->
						<div class="flex items-center gap-1.5">
							<Users class="w-4 h-4 text-gray-400 shrink-0" />
							<select
								:value="store.employeeFilter"
								class="text-sm border border-gray-200 rounded-md px-2.5 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-400 min-w-[150px]"
								@change="store.setEmployee($event.target.value)"
							>
								<option value="">{{ translate("All employees") }}</option>
								<option
									v-for="emp in store.employees"
									:key="emp.user"
									:value="emp.user"
								>
									{{ emp.full_name }}
								</option>
							</select>
						</div>

						<button
							class="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
							:title="translate('Refresh')"
							@click="store.fetchData()"
						>
							<RefreshCw
								class="w-4 h-4 text-gray-500"
								:class="{ 'animate-spin': store.loading }"
							/>
						</button>
					</div>

					<div class="flex items-center shrink-0">
						<OutlinerNav />
					</div>
				</div>
			</div>
		</header>

		<!-- ─── Loading ───────────────────────────────────────────────── -->
		<div
			v-if="store.loading && !store.hasData"
			class="flex items-center justify-center py-32"
		>
			<Loader2 class="w-8 h-8 text-purple-500 animate-spin" />
		</div>

		<!-- ─── Error ─────────────────────────────────────────────────── -->
		<div
			v-else-if="store.error"
			class="max-w-lg mx-auto py-16 text-center px-4"
		>
			<AlertTriangle class="w-10 h-10 text-red-400 mx-auto mb-3" />
			<p class="text-gray-600 mb-4">{{ store.error }}</p>
			<button
				class="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
				@click="store.fetchData()"
			>
				{{ translate("Try again") }}
			</button>
		</div>

		<!-- ─── Empty ─────────────────────────────────────────────────── -->
		<div
			v-else-if="store.hasData && store.employees.length === 0"
			class="max-w-md mx-auto py-16 text-center px-4"
		>
			<Users class="w-10 h-10 text-gray-300 mx-auto mb-3" />
			<p class="text-gray-500 text-sm">
				{{
					store.projectFilter
						? translate("No employees with allocations in this project or with free capacity this week.")
						: translate("No active employees found.")
				}}
			</p>
		</div>

		<!-- ─── Main grid ──────────────────────────────────────────────── -->
		<div
			v-else-if="store.hasData"
			class="w-full px-2 sm:px-4 lg:px-6 py-4"
		>
			<!-- Active project filter badge -->
			<div
				v-if="store.selectedProject"
				class="mb-3 inline-flex items-center gap-2 px-3 py-1.5 bg-purple-50 border border-purple-200 rounded-full text-sm text-purple-700 font-medium"
			>
				<CalendarDays class="w-3.5 h-3.5" />
				{{ store.selectedProject.project_name || store.selectedProject.name }}
				<button class="hover:text-purple-900 ml-0.5" @click="store.setProject('')">
					<X class="w-3.5 h-3.5" />
				</button>
			</div>

			<!-- Legend of projects present this week -->
			<div
				v-if="store.activeProjects.length > 0"
				class="mb-3 flex flex-wrap gap-2"
			>
				<span
					v-for="proj in store.activeProjects"
					:key="proj.project"
					class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium border"
					:style="{ backgroundColor: proj.color.bg, color: proj.color.text, borderColor: proj.color.bg }"
				>
					{{ proj.project_name }}
				</span>
			</div>

			<div class="overflow-x-auto">
				<table class="w-full border-collapse text-sm" style="min-width: 860px">
					<!-- ── Column headers ──────────────────────────────── -->
					<thead>
						<tr class="bg-white border-b border-gray-200">
							<th
								class="text-left px-4 py-3 font-semibold text-gray-700 w-44 sticky left-0 bg-white z-10 border-r border-gray-100"
							>
								{{ translate("Employee") }}
							</th>
							<th
								v-for="day in store.days"
								:key="day"
								class="text-center px-2 py-3 font-semibold text-gray-600 min-w-[148px]"
							>
								{{ dayLabel(day) }}
							</th>
							<th class="text-center px-4 py-3 font-semibold text-gray-600 w-28">
								{{ translate("Week") }}
							</th>
						</tr>
					</thead>

					<!-- ── Employee rows ───────────────────────────────── -->
					<tbody>
						<tr
							v-for="emp in store.employees"
							:key="emp.employee"
							class="border-b border-gray-100 transition-colors hover:bg-white/70"
							:class="emp.has_project_allocs ? 'bg-purple-50/20' : 'bg-white'"
						>
							<!-- Employee cell -->
							<td
								class="px-3 py-2.5 sticky left-0 z-10 border-r border-gray-100"
								:class="emp.has_project_allocs ? 'bg-purple-50/40' : 'bg-white'"
							>
								<div class="flex items-center gap-2">
									<div
										class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
										:class="emp.has_project_allocs ? 'bg-purple-500' : 'bg-gray-400'"
									>
										{{ emp.full_name.charAt(0).toUpperCase() }}
									</div>
									<div class="min-w-0">
										<div class="font-medium text-gray-800 text-xs leading-snug truncate">
											{{ emp.full_name }}
										</div>
										<!-- mini utilisation bar -->
										<div class="mt-0.5 h-1.5 w-24 bg-gray-200 rounded-full overflow-hidden">
											<div
												class="h-full rounded-full transition-all"
												:class="hoursBarColor(emp)"
												:style="{ width: hoursBarWidth(emp) }"
											></div>
										</div>
									</div>
								</div>
							</td>

							<!-- Day cells -->
							<td
								v-for="day in store.days"
								:key="day"
								class="px-1.5 py-1.5 align-top"
							>
								<div
									class="rounded-lg border p-1.5 min-h-[80px] flex flex-col gap-1 relative group transition-colors"
									:class="cellClass(emp.days[day])"
								>
									<!-- Overload badge -->
									<div
										v-if="emp.days[day].overloaded"
										class="flex items-center gap-1 text-red-600 text-xs font-semibold"
									>
										<AlertTriangle class="w-3 h-3 shrink-0" />
										{{ emp.days[day].planned_hours }}h / {{ store.dailyCapacity }}h
									</div>

									<!-- Allocation chips -->
									<button
										v-for="alloc in emp.days[day].allocations"
										:key="alloc.name"
										class="text-left text-xs px-2 py-1.5 rounded-md w-full font-medium hover:opacity-80 active:opacity-70 transition-opacity flex items-center justify-between gap-1 group/chip"
										:style="{
											backgroundColor: alloc.color.bg,
											color: alloc.color.text,
										}"
										:title="alloc.notes || alloc.project_name"
										@click="openEdit(alloc, emp, day)"
									>
										<span class="truncate block leading-tight">
											{{ alloc.project_name }}
										</span>
										<span class="shrink-0 font-semibold text-[11px]">
											{{ alloc.hours }}h
										</span>
									</button>

									<!-- Free hours badge -->
									<div
										v-if="emp.days[day].free_hours > 0"
										class="text-[11px] px-1.5 py-0.5 rounded border flex items-center gap-1 mt-auto"
										:class="freeHoursClass(emp.days[day].free_hours, store.dailyCapacity)"
									>
										<Clock class="w-3 h-3 shrink-0" />
										{{ emp.days[day].free_hours }}h
									</div>

									<!-- Add allocation button (on hover) -->
									<button
										class="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity w-5 h-5 rounded-full bg-purple-600 hover:bg-purple-700 text-white flex items-center justify-center"
										:title="translate('Add allocation')"
										@click.stop="store.openAddModal({ employee: emp.employee, employeeFullName: emp.full_name, day })"
									>
										<Plus class="w-3 h-3" />
									</button>
								</div>
							</td>

							<!-- Week total cell -->
							<td class="px-3 py-2.5 text-center align-middle">
								<div
									class="text-base font-semibold"
									:class="weeklyUtilClass(emp)"
								>
									{{ emp.weekly_planned_hours }}h
								</div>
								<div class="text-xs text-gray-400">/ {{ emp.weekly_capacity_hours }}h</div>
								<div
									v-if="emp.weekly_planned_hours > emp.weekly_capacity_hours"
									class="mt-1 text-xs text-red-500 flex items-center justify-center gap-0.5"
								>
									<AlertTriangle class="w-3 h-3" />
									{{ translate("Over") }}
								</div>
							</td>
						</tr>
					</tbody>
				</table>
			</div>

			<!-- Legend -->
			<div class="mt-4 flex flex-wrap gap-4 text-xs text-gray-500 px-1">
				<span class="flex items-center gap-1.5">
					<span class="w-3 h-3 rounded bg-red-200 border border-red-300 inline-block"></span>
					{{ translate("Overloaded (> {0}h)", [store.dailyCapacity]) }}
				</span>
				<span class="flex items-center gap-1.5">
					<span class="w-3 h-3 rounded bg-emerald-200 inline-block"></span>
					{{ translate("Free capacity") }}
				</span>
				<span class="flex items-center gap-1.5">
					<span class="w-3 h-3 rounded bg-amber-200 inline-block"></span>
					{{ translate("< 50% free") }}
				</span>
			</div>
		</div>

		<!-- ─── Add / Edit Allocation Modal ──────────────────────────── -->
		<Teleport to="body">
			<div
				v-if="store.modal.open"
				class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
				@click.self="store.closeModal()"
			>
				<div
					class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 relative"
					role="dialog"
				>
					<!-- Close -->
					<button
						class="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
						@click="store.closeModal()"
					>
						<X class="w-5 h-5" />
					</button>

					<!-- Title -->
					<h2 class="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
						<component
							:is="store.modal.mode === 'edit' ? Pencil : Plus"
							class="w-5 h-5 text-purple-600"
						/>
						{{
							store.modal.mode === "edit"
								? translate("Edit allocation")
								: translate("Add allocation")
						}}
					</h2>

					<p class="text-sm text-gray-500 mb-4">
						{{ store.modal.employeeFullName }}
						<span class="mx-1 text-gray-300">·</span>
						{{ store.modal.day }}
					</p>

					<div class="space-y-4">
						<!-- Project -->
						<div>
							<label class="block text-xs font-medium text-gray-700 mb-1">
								{{ translate("Project") }}
								<span class="text-red-500">*</span>
							</label>
							<select
								v-model="store.modal.project"
								class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
							>
								<option value="">{{ translate("Select project...") }}</option>
								<option
									v-for="p in store.projects"
									:key="p.name"
									:value="p.name"
								>
									{{ p.project_name || p.name }}
								</option>
							</select>
						</div>

						<!-- Hours -->
						<div>
							<label class="block text-xs font-medium text-gray-700 mb-1">
								{{ translate("Planned hours") }}
								<span class="text-red-500">*</span>
							</label>
							<div class="flex items-center gap-2">
								<input
									v-model="store.modal.hours"
									type="number"
									min="0"
									max="24"
									step="0.5"
									class="w-28 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 text-center font-semibold"
								/>
								<div class="flex gap-1">
									<button
										v-for="h in [2, 4, 6, 8]"
										:key="h"
										class="px-2.5 py-1 text-xs rounded-md border transition-colors"
										:class="
											Number(store.modal.hours) === h
												? 'bg-purple-600 text-white border-purple-600'
												: 'bg-gray-50 text-gray-600 border-gray-200 hover:border-purple-300'
										"
										@click="store.modal.hours = String(h)"
									>
										{{ h }}h
									</button>
								</div>
							</div>
						</div>

						<!-- Notes -->
						<div>
							<label class="block text-xs font-medium text-gray-700 mb-1">
								{{ translate("Notes") }}
							</label>
							<textarea
								v-model="store.modal.notes"
								rows="2"
								class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
								:placeholder="translate('Optional notes...')"
							/>
						</div>
					</div>

					<!-- Actions -->
					<div class="flex items-center justify-between mt-6">
						<!-- Delete (edit mode only) -->
						<button
							v-if="store.modal.mode === 'edit'"
							class="flex items-center gap-1.5 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
							:disabled="store.modal.deleting"
							@click="store.deleteAllocation(store.modal.allocationName)"
						>
							<Loader2 v-if="store.modal.deleting" class="w-4 h-4 animate-spin" />
							<Trash2 v-else class="w-4 h-4" />
							{{ translate("Delete") }}
						</button>
						<div v-else></div>

						<div class="flex gap-2">
							<button
								class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
								@click="store.closeModal()"
							>
								{{ translate("Cancel") }}
							</button>
							<button
								class="px-5 py-2 text-sm bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
								:disabled="store.modal.saving || !store.modal.project || !store.modal.hours"
								@click="store.saveModal()"
							>
								<Loader2 v-if="store.modal.saving" class="w-4 h-4 animate-spin" />
								{{ translate("Save") }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</Teleport>

		<BackToDeskButton />
	</div>
</template>
