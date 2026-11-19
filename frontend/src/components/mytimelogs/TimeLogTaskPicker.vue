<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useDebounceFn } from "@vueuse/core";
import { FolderOpen, History, ListChecks, Search, X } from "lucide-vue-next";
import { translate } from "../../utils/translation";

/**
 * First step of "Add time" on the My Time page: a time entry always belongs to
 * a task (create_timelog), so the user picks one here. Recently logged tasks
 * come from the page's own time logs; the rest are the user's open tasks.
 */
const props = defineProps({
	recentLogs: { type: Array, default: () => [] },
	fetchTasks: { type: Function, required: true },
});
const emit = defineEmits(["select", "close"]);

const query = ref("");
const tasks = ref([]);
const loading = ref(false);
const searchInput = ref(null);

const matches = (task) => {
	const q = query.value.trim().toLowerCase();
	if (!q) return true;
	return [task.subject, task.name, task.project_name, task.project]
		.filter(Boolean)
		.some((value) => String(value).toLowerCase().includes(q));
};

const recentTasks = computed(() => {
	const seen = new Set();
	const out = [];
	for (const log of props.recentLogs) {
		if (!log.task || seen.has(log.task)) continue;
		seen.add(log.task);
		out.push({
			name: log.task,
			subject: log.task_subject || log.task,
			project: log.project,
			project_name: log.project_name,
		});
		if (out.length >= 5) break;
	}
	return out.filter(matches);
});

const otherTasks = computed(() => {
	const recent = new Set(recentTasks.value.map((task) => task.name));
	return tasks.value.filter((task) => !recent.has(task.name) && matches(task));
});

async function load() {
	loading.value = true;
	try {
		tasks.value = await props.fetchTasks(query.value.trim());
	} catch (error) {
		console.error("Failed to load tasks:", error);
		tasks.value = [];
	} finally {
		loading.value = false;
	}
}

const debouncedLoad = useDebounceFn(load, 300);
watch(query, () => debouncedLoad());

function onKeydown(event) {
	if (event.key === "Escape") emit("close");
}

onMounted(async () => {
	document.addEventListener("keydown", onKeydown);
	await nextTick();
	searchInput.value?.focus();
	load();
});
onUnmounted(() => document.removeEventListener("keydown", onKeydown));
</script>

<template>
	<div
		class="fixed inset-0 z-50 flex items-end justify-end p-6 sm:items-center sm:justify-center"
		role="dialog"
		aria-modal="true"
		:aria-label="translate('Choose the task to log time on')"
	>
		<div class="absolute inset-0 bg-black/30" @click="emit('close')" />
		<div class="relative z-10 flex max-h-[80vh] w-full max-w-md flex-col rounded-2xl bg-white shadow-2xl">
			<div class="flex items-center justify-between px-6 pt-6">
				<h2 class="text-base font-semibold text-gray-900">{{ translate("Add time") }}</h2>
				<button
					type="button"
					class="rounded-lg p-1.5 text-gray-600 hover:bg-gray-100 hover:text-gray-900"
					:title="translate('Close')"
					:aria-label="translate('Close')"
					@click="emit('close')"
				>
					<X class="h-4 w-4" />
				</button>
			</div>
			<p class="px-6 pt-1 text-sm text-gray-700">{{ translate("Choose the task to log time on") }}</p>

			<div class="px-6 pt-4">
				<div class="relative">
					<Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-600" />
					<input
						ref="searchInput"
						v-model="query"
						type="text"
						:placeholder="translate('Search tasks...')"
						class="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
					/>
				</div>
			</div>

			<div class="mt-3 min-h-0 flex-1 overflow-y-auto px-3 pb-4">
				<template v-if="recentTasks.length">
					<p class="flex items-center gap-1.5 px-3 pb-1 pt-2 text-xs font-semibold uppercase tracking-wide text-gray-700">
						<History class="h-3.5 w-3.5" />
						{{ translate("Recently logged") }}
					</p>
					<button
						v-for="task in recentTasks"
						:key="`recent-${task.name}`"
						type="button"
						class="flex w-full flex-col items-start rounded-lg px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
						@click="emit('select', task)"
					>
						<span class="w-full truncate text-sm font-medium text-gray-900">{{ task.subject }}</span>
						<span class="flex w-full items-center gap-1 truncate text-xs text-gray-700">
							<FolderOpen class="h-3 w-3 flex-shrink-0" />
							{{ task.project_name || task.project || translate("No project") }}
						</span>
					</button>
				</template>

				<p class="flex items-center gap-1.5 px-3 pb-1 pt-3 text-xs font-semibold uppercase tracking-wide text-gray-700">
					<ListChecks class="h-3.5 w-3.5" />
					{{ translate("My Tasks") }}
				</p>
				<p v-if="loading && !otherTasks.length" class="px-3 py-2 text-sm text-gray-700">
					{{ translate("Loading...") }}
				</p>
				<p v-else-if="!otherTasks.length" class="px-3 py-2 text-sm text-gray-700">
					{{ translate("No tasks found") }}
				</p>
				<button
					v-for="task in otherTasks"
					:key="task.name"
					type="button"
					class="flex w-full flex-col items-start rounded-lg px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
					@click="emit('select', task)"
				>
					<span class="w-full truncate text-sm font-medium text-gray-900">{{ task.subject }}</span>
					<span class="flex w-full items-center gap-1 truncate text-xs text-gray-700">
						<FolderOpen class="h-3 w-3 flex-shrink-0" />
						{{ task.project_name || task.project || translate("No project") }}
					</span>
				</button>
			</div>
		</div>
	</div>
</template>
