<template>
	<Teleport to="body">
		<div v-if="show" class="fixed inset-0 z-50 overflow-y-auto" @keydown.esc="close">
			<div class="fixed inset-0 bg-black bg-opacity-50" @click="close"></div>

			<div class="flex min-h-full items-center justify-center p-4">
				<div
					class="relative w-full max-w-2xl rounded-lg bg-white shadow-xl"
					role="dialog"
					aria-modal="true"
					aria-labelledby="work-plan-modal-title"
				>
					<div class="flex items-start justify-between gap-4 border-b border-gray-200 px-6 py-4">
						<div class="min-w-0">
							<h3 id="work-plan-modal-title" class="text-lg font-semibold text-gray-900">
								{{ isEdit ? translate("Edit planned work") : translate("Plan work") }}
							</h3>
							<p class="mt-0.5 truncate text-sm text-gray-500">
								{{ employee?.employee_name }}
								<template v-if="isEdit"> · {{ formatDay(entry.date, LONG_DAY) }}</template>
							</p>
						</div>
						<button
							type="button"
							class="rounded-md p-1 text-gray-500 hover:bg-gray-100"
							:aria-label="translate('Close dialog')"
							@click="close"
						>
							<X class="h-5 w-5" />
						</button>
					</div>

					<div class="space-y-5 px-6 py-5">
						<!-- Project -->
						<div>
							<label class="mb-1 block text-sm font-medium text-gray-700">
								{{ translate("Project") }} <span class="text-red-500">*</span>
							</label>
							<div class="relative">
								<Search class="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
								<input
									ref="projectSearchRef"
									v-model="projectQuery"
									type="text"
									:placeholder="translate('Search projects...')"
									class="w-full rounded-md border border-gray-300 py-2 pl-9 pr-3 text-sm focus:border-violet-500 focus:ring-violet-500"
								/>
							</div>
							<div class="mt-2 max-h-48 overflow-y-auto rounded-md border border-gray-200">
								<div v-if="loadingProjects" class="px-3 py-3 text-sm text-gray-500">
									{{ translate("Loading...") }}
								</div>
								<div
									v-else-if="!filteredProjects.length"
									class="px-3 py-3 text-sm text-gray-500"
								>
									{{ translate("No projects found") }}
								</div>
								<template v-else>
									<template v-for="(group, groupIndex) in projectGroups" :key="groupIndex">
										<div
											v-if="group.label"
											class="sticky top-0 bg-gray-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-gray-500"
										>
											{{ group.label }}
										</div>
										<button
											v-for="project in group.projects"
											:key="project.name"
											type="button"
											class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition"
											:class="
												project.name === selectedProject
													? 'bg-violet-50 text-violet-900'
													: 'hover:bg-gray-50 text-gray-800'
											"
											@click="selectedProject = project.name"
										>
											<span
												class="h-2.5 w-2.5 shrink-0 rounded-full"
												:class="getProjectColor(project.name).dot"
											></span>
											<span class="min-w-0 flex-1 truncate">
												{{ project.project_name || project.name }}
											</span>
											<span class="shrink-0 text-xs text-gray-400">
												{{ project.customer || project.name }}
											</span>
											<Check
												v-if="project.name === selectedProject"
												class="h-4 w-4 shrink-0 text-violet-600"
											/>
										</button>
									</template>
								</template>
							</div>
						</div>

						<!-- Hours -->
						<div>
							<label class="mb-1 block text-sm font-medium text-gray-700">
								{{ isEdit ? translate("Hours") : translate("Hours per day") }}
								<span class="text-red-500">*</span>
							</label>
							<div v-if="!isEdit" class="mb-2 inline-flex rounded-md border border-gray-300 p-0.5 text-sm">
								<button
									type="button"
									class="rounded px-3 py-1"
									:class="hoursMode === 'fixed' ? 'bg-violet-600 text-white' : 'text-gray-600 hover:bg-gray-100'"
									@click="hoursMode = 'fixed'"
								>
									{{ translate("Fixed hours") }}
								</button>
								<button
									type="button"
									class="rounded px-3 py-1"
									:class="hoursMode === 'free' ? 'bg-violet-600 text-white' : 'text-gray-600 hover:bg-gray-100'"
									@click="hoursMode = 'free'"
								>
									{{ translate("All free time") }}
								</button>
							</div>
							<div v-if="isEdit || hoursMode === 'fixed'" class="flex flex-wrap items-center gap-2">
								<input
									v-model.number="hours"
									type="number"
									min="0.25"
									max="24"
									step="0.25"
									class="w-28 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-violet-500 focus:ring-violet-500"
								/>
								<button
									v-for="preset in HOUR_PRESETS"
									:key="preset"
									type="button"
									class="rounded-md border px-2.5 py-1.5 text-xs font-medium transition"
									:class="
										hours === preset
											? 'border-violet-500 bg-violet-50 text-violet-700'
											: 'border-gray-200 text-gray-600 hover:bg-gray-50'
									"
									@click="hours = preset"
								>
									{{ formatHours(preset) }} h
								</button>
								<button
									v-if="isEdit"
									type="button"
									class="rounded-md border border-gray-200 px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
									@click="hours = freeHours(entry.date) || hours"
								>
									{{ translate("Fill free time") }}
								</button>
							</div>
							<p v-else class="text-xs text-gray-500">
								{{ translate("Each selected day gets the hours the employee still has free on it.") }}
							</p>
						</div>

						<!-- Days -->
						<div v-if="!isEdit">
							<div class="mb-1 flex items-center justify-between gap-2">
								<label class="block text-sm font-medium text-gray-700">
									{{ translate("Days to plan") }} <span class="text-red-500">*</span>
								</label>
								<div class="flex gap-2 text-xs">
									<button
										type="button"
										class="text-violet-600 hover:underline"
										@click="selectAvailableDays"
									>
										{{ translate("All available days") }}
									</button>
									<button
										type="button"
										class="text-gray-500 hover:underline"
										@click="selectedDates = []"
									>
										{{ translate("Clear") }}
									</button>
								</div>
							</div>
							<div class="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-5">
								<button
									v-for="date in dayOptions"
									:key="date"
									type="button"
									class="rounded-md border px-2 py-1.5 text-left transition"
									:class="
										selectedDates.includes(date)
											? 'border-violet-500 bg-violet-50 ring-1 ring-violet-500'
											: 'border-gray-200 hover:bg-gray-50'
									"
									@click="toggleDate(date)"
								>
									<div class="text-xs font-semibold text-gray-800">{{ formatDay(date) }}</div>
									<div
										class="text-[11px]"
										:class="store.getAvailable(employee.name, date) > 0 ? 'text-gray-500' : 'text-amber-600'"
									>
										{{ dayOptionHint(date) }}
									</div>
								</button>
							</div>
						</div>

						<!-- Preview -->
						<div v-if="preview.length" class="rounded-md border border-gray-200">
							<div class="border-b border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
								{{ translate("Load after saving") }}
							</div>
							<div
								v-for="row in preview"
								:key="row.date"
								class="flex items-center justify-between gap-3 px-3 py-1.5 text-sm"
							>
								<span class="text-gray-700">{{ formatDay(row.date) }}</span>
								<span class="flex items-center gap-3">
									<span class="text-gray-500 tabular-nums">+{{ formatHours(row.hours) }} h</span>
									<span
										class="font-medium tabular-nums"
										:class="row.over ? 'text-red-600' : 'text-gray-800'"
									>
										<AlertTriangle v-if="row.over" class="-mt-0.5 inline h-3.5 w-3.5" />
										{{ formatHours(row.after) }} / {{ formatHours(row.available) }} h
									</span>
								</span>
							</div>
							<div
								v-if="skippedDays.length"
								class="border-t border-gray-100 px-3 py-1.5 text-xs text-amber-700"
							>
								{{ translate("No free time, skipped: {0}", [skippedDays.map((date) => formatDay(date)).join(", ")]) }}
							</div>
						</div>

						<!-- Note -->
						<div>
							<label class="mb-1 block text-sm font-medium text-gray-700">
								{{ translate("Note") }}
							</label>
							<textarea
								v-model="note"
								rows="2"
								:placeholder="translate('What should be done (optional)')"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-violet-500 focus:ring-violet-500"
							></textarea>
						</div>
					</div>

					<div class="flex items-center justify-between gap-3 border-t border-gray-200 px-6 py-4">
						<button
							v-if="isEdit"
							type="button"
							class="inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
							:disabled="saving"
							@click="remove"
						>
							<Trash2 class="h-4 w-4" />
							{{ translate("Delete") }}
						</button>
						<span v-else></span>
						<div class="flex gap-2">
							<button
								type="button"
								class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
								@click="close"
							>
								{{ translate("Cancel") }}
							</button>
							<button
								type="button"
								class="rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
								:disabled="!canSave || saving"
								@click="save"
							>
								{{ saving ? translate("Saving...") : translate("Save") }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { AlertTriangle, Check, Search, Trash2, X } from "lucide-vue-next";
import {
	useWorkPlanningStore,
	formatDay,
	formatHours,
	roundHours,
} from "../../stores/workPlanningStore";
import { getProjectColor } from "../../utils/projectColors";
import { translate } from "../../utils/translation";

const props = defineProps({
	show: { type: Boolean, default: false },
	employee: { type: Object, default: null },
	// Day the planner clicked; preselected when adding.
	date: { type: String, default: null },
	// Entry being edited; adding when empty.
	entry: { type: Object, default: null },
});

const emit = defineEmits(["close"]);

const HOUR_PRESETS = [1, 2, 4, 6, 8];
const LONG_DAY = { weekday: "long", day: "numeric", month: "long" };

const store = useWorkPlanningStore();

const projects = ref([]);
const loadingProjects = ref(false);
const projectQuery = ref("");
const selectedProject = ref("");
const hoursMode = ref("fixed");
const hours = ref(8);
const selectedDates = ref([]);
const note = ref("");
const saving = ref(false);
const projectSearchRef = ref(null);

const isEdit = computed(() => !!props.entry);

const filteredProjects = computed(() => {
	const query = projectQuery.value.trim().toLowerCase();
	if (!query) return projects.value;
	return projects.value.filter((project) =>
		[project.project_name, project.name, project.customer]
			.filter(Boolean)
			.some((value) => value.toLowerCase().includes(query))
	);
});

const projectGroups = computed(() => {
	const members = filteredProjects.value.filter((project) => project.is_member);
	const others = filteredProjects.value.filter((project) => !project.is_member);
	if (!members.length) return [{ label: null, projects: others }];
	return [
		{ label: translate("Employee's projects"), projects: members },
		{ label: others.length ? translate("Other projects") : null, projects: others },
	];
});

// Weekend days are offered only when shown in the grid or when the employee works then.
const dayOptions = computed(() =>
	store.dates.filter(
		(date) =>
			store.visibleDates.includes(date) ||
			store.getAvailable(props.employee?.name, date) > 0 ||
			date === props.date
	)
);

// Hours already planned that day, apart from what this dialog replaces.
function plannedWithoutReplaced(date) {
	return roundHours(
		store
			.getEntries(props.employee?.name, date)
			.filter((entry) =>
				isEdit.value ? entry.name !== props.entry.name : entry.project !== selectedProject.value
			)
			.reduce((sum, entry) => sum + entry.hours, 0)
	);
}

function freeHours(date) {
	return roundHours(
		Math.max(store.getAvailable(props.employee?.name, date) - plannedWithoutReplaced(date), 0)
	);
}

const allocations = computed(() => {
	if (isEdit.value) {
		return [{ date: props.entry.date, hours: Number(hours.value) || 0 }];
	}
	return store.dates
		.filter((date) => selectedDates.value.includes(date))
		.map((date) => ({
			date,
			hours: hoursMode.value === "free" ? freeHours(date) : Number(hours.value) || 0,
		}));
});

const skippedDays = computed(() =>
	allocations.value.filter((allocation) => allocation.hours <= 0).map((allocation) => allocation.date)
);

const preview = computed(() =>
	allocations.value
		.filter((allocation) => allocation.hours > 0)
		.map((allocation) => {
			const available = store.getAvailable(props.employee?.name, allocation.date);
			const after = roundHours(plannedWithoutReplaced(allocation.date) + allocation.hours);
			return { ...allocation, available, after, over: after - available > 0.001 };
		})
);

const canSave = computed(
	() =>
		!!selectedProject.value &&
		preview.value.length > 0 &&
		preview.value.every((row) => row.hours <= 24) &&
		(hoursMode.value === "free" || isEdit.value || skippedDays.value.length === 0)
);

function dayOptionHint(date) {
	const day = store.getDay(props.employee?.name, date);
	if (day.hours <= 0) {
		return day.reason || translate(day.status === "weekend" ? "Day off" : "Not available");
	}
	return translate("{0} h free", [formatHours(freeHours(date))]);
}

function toggleDate(date) {
	selectedDates.value = selectedDates.value.includes(date)
		? selectedDates.value.filter((selected) => selected !== date)
		: [...selectedDates.value, date];
}

function selectAvailableDays() {
	selectedDates.value = dayOptions.value.filter(
		(date) => store.getAvailable(props.employee?.name, date) > 0
	);
}

async function loadProjects() {
	loadingProjects.value = true;
	try {
		projects.value = await store.fetchProjects(props.employee?.name);
	} catch (err) {
		projects.value = [];
	} finally {
		loadingProjects.value = false;
	}
}

function reset() {
	projectQuery.value = "";
	hoursMode.value = "fixed";
	saving.value = false;
	if (props.entry) {
		selectedProject.value = props.entry.project;
		hours.value = props.entry.hours;
		note.value = props.entry.note || "";
		selectedDates.value = [props.entry.date];
	} else {
		selectedProject.value = "";
		note.value = "";
		selectedDates.value = props.date ? [props.date] : [];
		const free = props.date ? freeHours(props.date) : 0;
		hours.value = free > 0 ? free : store.defaultDailyHours;
	}
}

watch(
	() => props.show,
	async (show) => {
		if (!show) return;
		reset();
		loadProjects();
		await nextTick();
		projectSearchRef.value?.focus();
	}
);

function close() {
	emit("close");
}

async function save() {
	if (!canSave.value) return;
	saving.value = true;
	try {
		if (isEdit.value) {
			await store.updateEntry({
				name: props.entry.name,
				hours: allocations.value[0].hours,
				project: selectedProject.value,
				note: note.value,
			});
		} else {
			await store.saveEntries({
				employee: props.employee.name,
				project: selectedProject.value,
				allocations: preview.value.map(({ date, hours }) => ({ date, hours })),
				note: note.value.trim() || null,
			});
		}
		close();
	} catch (err) {
		// apiCall already showed the error
	} finally {
		saving.value = false;
	}
}

async function remove() {
	if (!window.confirm(translate("Delete this plan entry?"))) return;
	saving.value = true;
	try {
		await store.deleteEntry(props.entry.name);
		close();
	} catch (err) {
		// apiCall already showed the error
	} finally {
		saving.value = false;
	}
}
</script>
