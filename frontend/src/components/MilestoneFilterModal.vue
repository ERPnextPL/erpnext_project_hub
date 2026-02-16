<script setup>
import { computed, ref, watch } from "vue";
import { Search, X } from "lucide-vue-next";
import { translate } from "../utils/translation";

const props = defineProps({
	show: {
		type: Boolean,
		default: false,
	},
	milestones: {
		type: Array,
		default: () => [],
	},
	selectedMilestones: {
		type: Array,
		default: () => [],
	},
});

const emit = defineEmits(["close", "apply"]);

const search = ref("");
const sortBy = ref("deadline");
const includeDone = ref(false);
const localSelected = ref([]);

watch(
	() => [props.show, props.selectedMilestones],
	() => {
		if (!props.show) return;
		localSelected.value = [...props.selectedMilestones];
		search.value = "";
		sortBy.value = "deadline";
		includeDone.value = false;
	},
	{ immediate: true, deep: true }
);

const visibleMilestones = computed(() => {
	const query = search.value.trim().toLowerCase();
	let list = [...props.milestones];

	if (!includeDone.value) {
		list = list.filter((m) => m.health !== "completed" && m.health !== "cancelled");
	}

	if (query) {
		list = list.filter((m) => (m.milestone_name || "").toLowerCase().includes(query));
	}

	if (sortBy.value === "name") {
		list.sort((a, b) => (a.milestone_name || "").localeCompare(b.milestone_name || ""));
	} else if (sortBy.value === "progress") {
		list.sort((a, b) => (b.progress || 0) - (a.progress || 0));
	} else {
		list.sort((a, b) => {
			const aDate = a.milestone_date ? new Date(a.milestone_date).getTime() : Number.POSITIVE_INFINITY;
			const bDate = b.milestone_date ? new Date(b.milestone_date).getTime() : Number.POSITIVE_INFINITY;
			return aDate - bDate;
		});
	}

	return list;
});

function isSelected(name) {
	return localSelected.value.includes(name);
}

function toggleSelection(name) {
	if (!name) return;
	if (localSelected.value.includes(name)) {
		localSelected.value = localSelected.value.filter((v) => v !== name);
	} else {
		localSelected.value = [...localSelected.value, name];
	}
}

function setPresetAll() {
	localSelected.value = visibleMilestones.value.map((m) => m.name);
}

function setPresetActive() {
	localSelected.value = props.milestones
		.filter((m) => m.health !== "completed" && m.health !== "cancelled")
		.map((m) => m.name);
}

function setPresetOverdue() {
	localSelected.value = props.milestones
		.filter((m) => m.health === "overdue")
		.map((m) => m.name);
}

function setPresetNoDeadline() {
	localSelected.value = props.milestones
		.filter((m) => !m.milestone_date)
		.map((m) => m.name);
}

function clearSelection() {
	localSelected.value = [];
}

function formatDate(dateStr) {
	if (!dateStr) return translate("No deadline");
	const date = new Date(dateStr);
	return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function applyAndClose() {
	emit("apply", [...localSelected.value]);
	emit("close");
}
</script>

<template>
	<Teleport to="body">
		<Transition name="fade">
			<div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
				<div class="absolute inset-0 bg-black/40" @click="emit('close')" />
				<div class="relative w-full max-w-2xl bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700">
					<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
						<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
							{{ translate("Filter milestones") }}
						</h3>
						<button
							type="button"
							class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
							@click="emit('close')"
						>
							<X class="w-4 h-4" />
						</button>
					</div>

					<div class="p-4 space-y-3">
						<div class="flex gap-2">
							<div class="relative flex-1">
								<Search class="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
								<input
									v-model="search"
									type="text"
									:placeholder="translate('Search milestone...')"
									class="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
								/>
							</div>
							<select
								v-model="sortBy"
								class="px-2 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
							>
								<option value="deadline">{{ translate("Sort: deadline") }}</option>
								<option value="name">{{ translate("Sort: name") }}</option>
								<option value="progress">{{ translate("Sort: progress") }}</option>
							</select>
							<button
								type="button"
								class="px-2.5 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
								@click="includeDone = !includeDone"
							>
								{{ includeDone ? translate("Hide done") : translate("Show done") }}
							</button>
						</div>

						<div class="flex flex-wrap gap-2">
							<button type="button" class="text-xs px-2 py-1 rounded border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700" @click="setPresetAll">
								{{ translate("All visible") }}
							</button>
							<button type="button" class="text-xs px-2 py-1 rounded border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700" @click="setPresetActive">
								{{ translate("Active only") }}
							</button>
							<button type="button" class="text-xs px-2 py-1 rounded border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700" @click="setPresetOverdue">
								{{ translate("Overdue") }}
							</button>
							<button type="button" class="text-xs px-2 py-1 rounded border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700" @click="setPresetNoDeadline">
								{{ translate("No deadline") }}
							</button>
							<button type="button" class="text-xs px-2 py-1 rounded border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700" @click="clearSelection">
								{{ translate("Clear") }}
							</button>
						</div>

						<div class="max-h-[45vh] overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
							<label
								v-for="milestone in visibleMilestones"
								:key="milestone.name"
								class="flex items-center gap-3 px-3 py-2 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
							>
								<input
									type="checkbox"
									:checked="isSelected(milestone.name)"
									@change="toggleSelection(milestone.name)"
									class="rounded border-gray-300 text-blue-600"
								/>
								<div class="min-w-0 flex-1">
									<div class="font-medium text-gray-900 dark:text-gray-100 truncate">
										{{ milestone.milestone_name }}
									</div>
									<div class="text-xs text-gray-500 dark:text-gray-400">
										{{ formatDate(milestone.milestone_date) }}
										· {{ milestone.completed_tasks || 0 }}/{{ milestone.total_tasks || 0 }} {{ translate("tasks") }}
									</div>
								</div>
							</label>
							<div v-if="visibleMilestones.length === 0" class="px-3 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
								{{ translate("No milestones found") }}
							</div>
						</div>
					</div>

					<div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
						<div class="text-xs text-gray-500 dark:text-gray-400">
							{{ translate("{count} selected", { count: localSelected.length }) }}
						</div>
						<div class="flex items-center gap-2">
							<button type="button" class="px-3 py-1.5 text-sm rounded-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700" @click="emit('close')">
								{{ translate("Cancel") }}
							</button>
							<button type="button" class="px-3 py-1.5 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700" @click="applyAndClose">
								{{ translate("Apply filters") }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
