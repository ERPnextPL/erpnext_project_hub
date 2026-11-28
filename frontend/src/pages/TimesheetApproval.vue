<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
	AlertCircle,
	Briefcase,
	CheckCircle2,
	ChevronRight,
	ClipboardCheck,
	Filter,
	RefreshCw,
	Search,
	UserRound,
	X,
} from "lucide-vue-next";
import OutlinerNav from "../components/OutlinerNav.vue";
import BackToDeskButton from "../components/BackToDeskButton.vue";
import { useTimesheetApprovalStore } from "../stores/timesheetApprovalStore";
import { translate } from "../utils/translation";

const store = useTimesheetApprovalStore();
const filters = reactive({ search: "", project: "", employee: "", start_date: "", end_date: "" });
const selectedNames = ref([]);
const selectedItem = ref(null);
const rejectDialogOpen = ref(false);
const rejectReason = ref("");
const rejectTargets = ref([]);
const actionLoading = ref(false);

const locale = computed(() => window.frappe?.boot?.lang || navigator.language || "en-US");
const numberFormatter = computed(
	() => new Intl.NumberFormat(locale.value, { maximumFractionDigits: 2 })
);

const groupedItems = computed(() => {
	const groups = new Map();
	store.items.forEach((item) => {
		const key = item.projects.length === 1 ? item.projects[0].name : "__multiple__";
		const label = item.projects.length === 1 ? item.projects[0].label : translate("Multiple projects");
		if (!groups.has(key)) groups.set(key, { key, label, items: [] });
		groups.get(key).items.push(item);
	});
	return [...groups.values()];
});

function formatHours(value) {
	return numberFormatter.value.format(Number(value) || 0);
}

function formatDate(value) {
	if (!value) return "—";
	const date = new Date(`${value}T00:00:00`);
	return new Intl.DateTimeFormat(locale.value, { day: "2-digit", month: "short" }).format(date);
}

function formatDateTime(value) {
	if (!value) return "—";
	const date = new Date(String(value).replace(" ", "T"));
	return new Intl.DateTimeFormat(locale.value, {
		day: "2-digit",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
	}).format(date);
}

function formatPeriod(item) {
	const start = formatDate(item.start_date);
	const end = formatDate(item.end_date);
	return start === end ? start : `${start} – ${end}`;
}

function projectNames(item) {
	return item.projects.map((project) => project.label).join(", ");
}

function refresh() {
	selectedNames.value = [];
	selectedItem.value = null;
	return store.fetchQueue({ ...filters });
}

function resetFilters() {
	Object.assign(filters, { search: "", project: "", employee: "", start_date: "", end_date: "" });
	return refresh();
}

function toggleSelected(name) {
	selectedNames.value = selectedNames.value.includes(name)
		? selectedNames.value.filter((item) => item !== name)
		: [...selectedNames.value, name];
}

function openDetails(item) {
	selectedItem.value = item;
}

function closeDetails() {
	selectedItem.value = null;
}

async function approve(names) {
	if (!names.length || actionLoading.value) return;
	const hours = names.reduce((sum, name) => {
		const item = store.items.find((entry) => entry.name === name);
		return sum + (Number(item?.total_hours) || 0);
	}, 0);
	const question = translate("Approve {0} timesheets ({1} h)?", [names.length, formatHours(hours)]);
	if (!confirm(question)) return;

	actionLoading.value = true;
	try {
		for (const name of names) await store.approve(name);
		frappe.show_alert({ message: translate("Timesheets approved"), indicator: "green" });
		await refresh();
	} catch (error) {
		console.error("Failed to approve timesheets:", error);
	} finally {
		actionLoading.value = false;
	}
}

function openRejectDialog(names) {
	if (!names.length || actionLoading.value) return;
	rejectTargets.value = [...names];
	rejectReason.value = "";
	rejectDialogOpen.value = true;
}

async function confirmReject() {
	const reason = rejectReason.value.trim();
	if (!reason || actionLoading.value) return;

	actionLoading.value = true;
	try {
		for (const name of rejectTargets.value) await store.reject(name, reason);
		rejectDialogOpen.value = false;
		frappe.show_alert({ message: translate("Timesheets rejected"), indicator: "orange" });
		await refresh();
	} catch (error) {
		console.error("Failed to reject timesheets:", error);
	} finally {
		actionLoading.value = false;
	}
}

onMounted(() => store.fetchQueue());
</script>

<template>
	<div class="min-h-screen bg-slate-50 text-slate-900">
		<header class="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
			<div class="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
				<div class="flex min-w-0 items-center gap-3">
					<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
						<ClipboardCheck class="h-5 w-5" />
					</div>
					<div class="min-w-0">
						<h1 class="truncate text-lg font-semibold text-slate-900">{{ translate("Time approval") }}</h1>
						<p class="truncate text-xs text-slate-500 max-sm:hidden">{{ translate("Review your project's pending hours") }}</p>
					</div>
				</div>
				<div class="flex items-center gap-2">
					<button
						type="button"
						class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:opacity-50"
						:disabled="store.loading"
						:title="translate('Refresh')"
						@click="refresh"
					>
						<RefreshCw class="h-4 w-4" :class="store.loading ? 'animate-spin' : ''" />
					</button>
					<OutlinerNav />
				</div>
			</div>
		</header>

		<main class="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6 lg:px-8">
			<div class="grid gap-3 sm:grid-cols-3">
				<div class="rounded-2xl border border-orange-200 bg-orange-50 p-4">
					<p class="text-xs font-semibold uppercase tracking-wide text-orange-700">{{ translate("To review") }}</p>
					<p class="mt-1 text-3xl font-bold text-orange-950">{{ store.total }}</p>
					<p class="text-xs text-orange-700">{{ translate("timesheets") }}</p>
				</div>
				<div class="rounded-2xl border border-blue-200 bg-blue-50 p-4">
					<p class="text-xs font-semibold uppercase tracking-wide text-blue-700">{{ translate("Hours waiting") }}</p>
					<p class="mt-1 text-3xl font-bold text-blue-950">{{ formatHours(store.totalHours) }}</p>
					<p class="text-xs text-blue-700">{{ translate("hours") }}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-white p-4">
					<p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ translate("Selected") }}</p>
					<p class="mt-1 text-3xl font-bold text-slate-900">{{ selectedNames.length }}</p>
					<p class="text-xs text-slate-500">{{ translate("timesheets") }}</p>
				</div>
			</div>

			<section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
				<div class="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
					<Filter class="h-4 w-4 text-slate-500" />
					{{ translate("Find timesheets") }}
				</div>
				<div class="grid gap-3 md:grid-cols-5">
					<label class="relative md:col-span-2">
						<Search class="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
						<input v-model="filters.search" class="hub-input pl-9" :placeholder="translate('Search employee, project or task')" @keyup.enter="refresh" />
					</label>
					<select v-model="filters.project" class="hub-input">
						<option value="">{{ translate("All projects") }}</option>
						<option v-for="project in store.projects" :key="project.name" :value="project.name">{{ project.label }}</option>
					</select>
					<select v-model="filters.employee" class="hub-input">
						<option value="">{{ translate("All employees") }}</option>
						<option v-for="employee in store.employees" :key="employee.name" :value="employee.name">{{ employee.label }}</option>
					</select>
					<div class="flex gap-2">
						<input v-model="filters.start_date" type="date" class="hub-input min-w-0" :title="translate('From date')" />
						<input v-model="filters.end_date" type="date" class="hub-input min-w-0" :title="translate('To date')" />
					</div>
				</div>
				<div class="mt-3 flex flex-wrap gap-2">
					<button type="button" class="hub-button-primary" @click="refresh">{{ translate("Apply filters") }}</button>
					<button type="button" class="hub-button-secondary" @click="resetFilters">{{ translate("Reset") }}</button>
				</div>
			</section>

			<div v-if="store.error" class="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
				<AlertCircle class="h-4 w-4 shrink-0" />
				{{ store.error }}
			</div>
			<div v-else-if="store.loading" class="rounded-2xl border border-slate-200 bg-white py-16 text-center text-sm text-slate-500">
				<RefreshCw class="mx-auto mb-3 h-6 w-6 animate-spin text-orange-500" />
				{{ translate("Loading approval queue...") }}
			</div>
			<div v-else-if="!store.items.length" class="rounded-2xl border border-slate-200 bg-white py-16 text-center">
				<CheckCircle2 class="mx-auto mb-3 h-10 w-10 text-emerald-500" />
				<h2 class="font-semibold text-slate-900">{{ translate("All caught up") }}</h2>
				<p class="mt-1 text-sm text-slate-500">{{ translate("There are no timesheets waiting for your approval.") }}</p>
			</div>

			<section v-for="group in groupedItems" v-else :key="group.key" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
				<div class="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-3">
					<div class="flex min-w-0 items-center gap-2">
						<Briefcase class="h-4 w-4 shrink-0 text-orange-500" />
						<h2 class="truncate text-sm font-semibold text-slate-800">{{ group.label }}</h2>
						<span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600">{{ group.items.length }}</span>
					</div>
				</div>
				<div class="overflow-x-auto max-md:hidden">
					<table class="w-full text-left text-sm">
						<thead class="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
							<tr>
								<th class="w-12 px-4 py-3"><input type="checkbox" :checked="group.items.every((item) => selectedNames.includes(item.name))" @change="group.items.forEach((item) => selectedNames.includes(item.name) !== $event.target.checked && toggleSelected(item.name))" /></th>
								<th class="px-3 py-3">{{ translate("Employee") }}</th>
								<th class="px-3 py-3">{{ translate("Period") }}</th>
								<th class="px-3 py-3">{{ translate("Hours") }}</th>
								<th class="px-3 py-3">{{ translate("Entries") }}</th>
								<th class="px-3 py-3">{{ translate("Sent") }}</th>
								<th class="w-12 px-3 py-3"></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-100">
							<tr v-for="item in group.items" :key="item.name" class="cursor-pointer hover:bg-orange-50/50" :class="selectedNames.includes(item.name) ? 'bg-orange-50' : ''" @click="openDetails(item)">
								<td class="px-4 py-4" @click.stop><input type="checkbox" :checked="selectedNames.includes(item.name)" @change="toggleSelected(item.name)" /></td>
								<td class="px-3 py-4"><div class="flex items-center gap-2"><UserRound class="h-4 w-4 text-slate-400" /><span class="font-medium text-slate-800">{{ item.employee_name || item.employee || translate("Unknown employee") }}</span></div></td>
								<td class="px-3 py-4 text-slate-600">{{ formatPeriod(item) }}</td>
								<td class="px-3 py-4 font-semibold text-slate-900">{{ formatHours(item.total_hours) }} h</td>
								<td class="px-3 py-4 text-slate-600">{{ item.entries.length }}</td>
								<td class="px-3 py-4 text-xs text-slate-500">{{ formatDateTime(item.approval_requested_on) }}</td>
								<td class="px-3 py-4 text-right"><ChevronRight class="ml-auto h-4 w-4 text-slate-400" /></td>
							</tr>
						</tbody>
					</table>
				</div>
				<div class="divide-y divide-slate-100 md:hidden">
					<button v-for="item in group.items" :key="item.name" type="button" class="flex w-full items-center gap-3 p-4 text-left hover:bg-orange-50/50" @click="openDetails(item)">
						<input type="checkbox" :checked="selectedNames.includes(item.name)" @click.stop @change="toggleSelected(item.name)" />
						<div class="min-w-0 flex-1"><p class="truncate font-medium text-slate-800">{{ item.employee_name || item.employee }}</p><p class="mt-1 text-xs text-slate-500">{{ formatPeriod(item) }} · {{ item.entries.length }} {{ translate("entries") }}</p></div>
						<div class="text-right"><p class="font-semibold text-slate-900">{{ formatHours(item.total_hours) }} h</p><p class="text-xs text-slate-500">{{ formatDateTime(item.approval_requested_on) }}</p></div>
						<ChevronRight class="h-4 w-4 shrink-0 text-slate-400" />
					</button>
				</div>
			</section>

			<div v-if="selectedNames.length" class="sticky bottom-4 z-10 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-xl backdrop-blur">
				<span class="text-sm font-medium text-slate-700">{{ selectedNames.length }} {{ translate("selected") }}</span>
				<div class="flex gap-2"><button type="button" class="hub-button-secondary" :disabled="actionLoading" @click="openRejectDialog(selectedNames)">{{ translate("Reject") }}</button><button type="button" class="hub-button-primary" :disabled="actionLoading" @click="approve(selectedNames)">{{ translate("Approve selected") }}</button></div>
			</div>
		</main>

		<div v-if="selectedItem" class="fixed inset-0 z-30 bg-slate-900/30" @click="closeDetails">
			<aside class="absolute right-0 top-0 flex h-full w-full max-w-xl flex-col bg-white shadow-2xl" @click.stop>
				<div class="flex items-start justify-between border-b border-slate-200 p-5"><div><p class="text-xs font-semibold uppercase tracking-wide text-orange-600">{{ translate("Pending approval") }}</p><h2 class="mt-1 text-lg font-semibold text-slate-900">{{ selectedItem.employee_name || selectedItem.employee }}</h2><p class="mt-1 text-sm text-slate-500">{{ projectNames(selectedItem) }} · {{ formatPeriod(selectedItem) }}</p></div><button type="button" class="rounded-lg p-2 text-slate-500 hover:bg-slate-100" @click="closeDetails"><X class="h-5 w-5" /></button></div>
				<div class="flex-1 space-y-5 overflow-y-auto p-5"><div class="grid grid-cols-2 gap-3"><div class="rounded-xl bg-slate-50 p-3"><p class="text-xs text-slate-500">{{ translate("Total hours") }}</p><p class="mt-1 text-2xl font-bold text-slate-900">{{ formatHours(selectedItem.total_hours) }} h</p></div><div class="rounded-xl bg-slate-50 p-3"><p class="text-xs text-slate-500">{{ translate("Sent") }}</p><p class="mt-1 text-sm font-semibold text-slate-900">{{ formatDateTime(selectedItem.approval_requested_on) }}</p></div></div><div class="space-y-3"><h3 class="text-sm font-semibold text-slate-800">{{ translate("Time entries") }}</h3><div v-for="entry in selectedItem.entries" :key="entry.name" class="rounded-xl border border-slate-200 p-3"><div class="flex items-start justify-between gap-3"><div class="min-w-0"><p class="font-medium text-slate-800">{{ entry.task_subject || translate("No task") }}</p><p class="mt-1 text-xs text-slate-500">{{ entry.project_name || translate("No project") }} · {{ entry.activity_type || translate("No activity") }}</p></div><span class="shrink-0 font-semibold text-slate-900">{{ formatHours(entry.hours) }} h</span></div><p class="mt-2 text-xs text-slate-500">{{ formatDateTime(entry.from_time) }} – {{ formatDateTime(entry.to_time) }}</p><p v-if="entry.description" class="mt-2 whitespace-pre-wrap text-sm text-slate-700">{{ entry.description }}</p></div></div></div>
				<div class="flex gap-2 border-t border-slate-200 p-5"><button type="button" class="hub-button-secondary flex-1" :disabled="actionLoading" @click="openRejectDialog([selectedItem.name])">{{ translate("Reject") }}</button><button type="button" class="hub-button-primary flex-1" :disabled="actionLoading" @click="approve([selectedItem.name])">{{ translate("Approve") }}</button></div>
			</aside>
		</div>

		<div v-if="rejectDialogOpen" class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 p-4">
			<div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl"><div class="flex items-center justify-between"><h2 class="text-lg font-semibold text-slate-900">{{ translate("Reject timesheet") }}</h2><button type="button" class="rounded-lg p-2 text-slate-500 hover:bg-slate-100" @click="rejectDialogOpen = false"><X class="h-5 w-5" /></button></div><p class="mt-2 text-sm text-slate-500">{{ translate("The employee will see this reason and can correct the hours.") }}</p><textarea v-model="rejectReason" rows="4" class="hub-input mt-4 resize-none" :placeholder="translate('Explain what needs to be corrected')"></textarea><div class="mt-4 flex justify-end gap-2"><button type="button" class="hub-button-secondary" @click="rejectDialogOpen = false">{{ translate("Cancel") }}</button><button type="button" class="hub-button-danger" :disabled="!rejectReason.trim() || actionLoading" @click="confirmReject">{{ translate("Reject") }}</button></div></div>
		</div>
		<BackToDeskButton />
	</div>
</template>

<style scoped>
.hub-input {
	@apply w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-orange-500 focus:ring-2 focus:ring-orange-100;
}

.hub-button-primary,
.hub-button-secondary,
.hub-button-danger {
	@apply rounded-lg px-3 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50;
}

.hub-button-primary {
	@apply bg-orange-600 text-white hover:bg-orange-700;
}

.hub-button-secondary {
	@apply border border-slate-300 bg-white text-slate-700 hover:bg-slate-50;
}

.hub-button-danger {
	@apply bg-red-600 text-white hover:bg-red-700;
}
</style>
