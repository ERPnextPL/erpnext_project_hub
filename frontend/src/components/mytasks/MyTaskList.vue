<script setup>
import { computed } from "vue";
import { useMyTasksStore } from "../../stores/myTasksStore";
import MyTaskRowDesktop from "./MyTaskRowDesktop.vue";
import MyTaskCardMobile from "./MyTaskCardMobile.vue";
import { useWindowSize } from "@vueuse/core";
import { ArrowUp, ArrowDown } from "lucide-vue-next";

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text) => {
	return typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
		? realWindow.__(text)
		: text;
};

const store = useMyTasksStore();
const { width } = useWindowSize();
const isMobile = computed(() => width.value < 768);

const props = defineProps({
	onOpenTimeLogModal: {
		type: Function,
		required: true,
	},
});

const statusOrder = ["Overdue", "Open", "Working", "Pending Review", "Completed", "Cancelled"];
const statusLabels = {
	Overdue: translate("Overdue"),
	Open: translate("Open"),
	Working: translate("Working"),
	"Pending Review": translate("Pending Review"),
	Completed: translate("Completed"),
	Cancelled: translate("Cancelled"),
};

const tasksByName = computed(() => {
	const m = new Map();
	for (const t of store.tasks) m.set(t.name, t);
	return m;
});

const childrenByParent = computed(() => {
	const m = new Map();
	for (const t of store.tasks) {
		if (!t.parent_task) continue;
		if (!m.has(t.parent_task)) m.set(t.parent_task, []);
		m.get(t.parent_task).push(t);
	}
	return m;
});

function isExpanded(taskName) {
	return store.expandedParents?.has(taskName);
}

function hasChildren(taskName) {
	return (childrenByParent.value.get(taskName) || []).length > 0;
}

function buildHierarchyItems(sectionTasks) {
	const sectionNames = new Set(sectionTasks.map((t) => t.name));
	const usedContextParents = new Set();
	const items = [];

	for (const t of sectionTasks) {
		if (t.parent_task && !sectionNames.has(t.parent_task)) {
			if (!usedContextParents.has(t.parent_task)) {
				usedContextParents.add(t.parent_task);
				const parent = tasksByName.value.get(t.parent_task);
				items.push({
					type: "context",
					key: `ctx:${t.parent_task}`,
					name: t.parent_task,
					subject: parent?.subject || t.parent_subject || t.parent_task,
				});
			}
			items.push({ type: "task", key: t.name, task: t, indent: 1 });
			continue;
		}

		if (!t.parent_task || !sectionNames.has(t.parent_task)) {
			items.push({ type: "task", key: t.name, task: t, indent: 0 });
			if (isExpanded(t.name)) {
				const children = (childrenByParent.value.get(t.name) || []).filter((c) =>
					sectionNames.has(c.name)
				);
				for (const c of children) {
					items.push({ type: "task", key: c.name, task: c, indent: 1 });
				}
			}
		}
	}

	return items;
}

const sections = computed(() => {
	const all = store.tasks || [];
	if (!store.viewOptions?.groupByStatus) {
		return [{ key: "all", label: null, tasks: all }];
	}

	const groups = new Map();
	for (const s of statusOrder) groups.set(s, []);
	for (const t of all) {
		const s = t.status || "Open";
		if (!groups.has(s)) groups.set(s, []);
		groups.get(s).push(t);
	}

	return statusOrder
		.filter((s) => (groups.get(s) || []).length > 0)
		.map((s) => ({ key: s, label: statusLabels[s] || s, tasks: groups.get(s) || [] }));
});

function getSortIcon(column) {
	if (store.filters.sortBy !== column) return null;
	return store.filters.sortOrder === "asc" ? ArrowUp : ArrowDown;
}

function handleSort(column) {
	store.setSorting(column);
}
</script>

<template>
	<div>
		<!-- Task list -->
		<div class="bg-white rounded-lg border border-gray-200 overflow-visible">
			<!-- Table header (desktop only) -->
			<div
				v-if="!isMobile"
				class="grid grid-cols-12 gap-4 px-4 py-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wider"
			>
				<button
					@click="handleSort('subject')"
					class="col-span-4 text-left hover:text-gray-700 transition-colors flex items-center gap-1"
				>
					Zadanie
					<component
						v-if="getSortIcon('subject')"
						:is="getSortIcon('subject')"
						class="w-3 h-3"
					/>
				</button>
				<button
					@click="handleSort('project')"
					class="col-span-2 text-left hover:text-gray-700 transition-colors flex items-center gap-1"
				>
					Projekt
					<component
						v-if="getSortIcon('project')"
						:is="getSortIcon('project')"
						class="w-3 h-3"
					/>
				</button>
				<button
					@click="handleSort('status')"
					class="col-span-2 text-left hover:text-gray-700 transition-colors flex items-center gap-1"
				>
					Status
					<component
						v-if="getSortIcon('status')"
						:is="getSortIcon('status')"
						class="w-3 h-3"
					/>
				</button>
				<button
					@click="handleSort('priority')"
					class="col-span-2 text-left hover:text-gray-700 transition-colors flex items-center gap-1"
				>
					Priorytet
					<component
						v-if="getSortIcon('priority')"
						:is="getSortIcon('priority')"
						class="w-3 h-3"
					/>
				</button>
				<button
					@click="handleSort('due_date')"
					class="col-span-2 text-left hover:text-gray-700 transition-colors flex items-center gap-1"
				>
					Termin
					<component
						v-if="getSortIcon('due_date')"
						:is="getSortIcon('due_date')"
						class="w-3 h-3"
					/>
				</button>
			</div>

			<!-- Task rows -->
			<div class="divide-y divide-gray-100">
				<template v-for="section in sections" :key="section.key">
					<div
						v-if="section.label"
						class="px-4 py-2 text-xs font-semibold text-gray-600 bg-gray-50 border-y border-gray-200"
					>
						{{ section.label }} ({{ section.tasks.length }})
					</div>

					<!-- Desktop: hierarchy + context rows -->
					<div v-if="!isMobile">
						<template
							v-for="item in store.viewOptions?.showHierarchy
								? buildHierarchyItems(section.tasks)
								: section.tasks.map((t) => ({
										type: 'task',
										key: t.name,
										task: t,
										indent: 0,
								  }))"
							:key="item.key"
						>
							<div
								v-if="item.type === 'context'"
								class="grid grid-cols-12 gap-4 px-4 py-2 bg-gray-50 text-xs text-gray-600"
							>
								<div class="col-span-12 truncate">↳ {{ item.subject }}</div>
							</div>
							<MyTaskRowDesktop
								v-else
								:task="item.task"
								:indent-level="item.indent"
								:hierarchy-enabled="store.viewOptions?.showHierarchy"
								:has-children="
									store.viewOptions?.showHierarchy && hasChildren(item.task.name)
								"
								:is-expanded="
									store.viewOptions?.showHierarchy && isExpanded(item.task.name)
								"
								@toggle-expand="store.toggleExpandParent"
								@open-time-log-modal="props.onOpenTimeLogModal"
							/>
						</template>
					</div>

					<!-- Mobile: flat list -->
					<template v-else>
						<MyTaskCardMobile
							v-for="task in section.tasks"
							:key="task.name"
							:task="task"
						/>
					</template>
				</template>
			</div>
		</div>

		<!-- Load more / pagination info -->
		<div v-if="store.tasks.length > 0" class="mt-4 text-center text-sm text-gray-500">
			{{ translate("Showing") }} {{ store.tasks.length }} {{ translate("of") }}
			{{ store.total }} {{ translate("tasks") }}
		</div>
	</div>
</template>
