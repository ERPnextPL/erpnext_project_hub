<script setup>
import { ref, computed, onMounted } from "vue";
import { useTaskStore } from "../stores/taskStore";
import { AlertCircle, User, Flag, Calendar, X } from "lucide-vue-next";
import { getStatusOption } from "../utils/taskStatus";

const props = defineProps({
	project: {
		type: Object,
		default: null,
	},
});

const emit = defineEmits(["filter-change", "close"]);

const store = useTaskStore();
const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text) => {
	return typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
		? realWindow.__(text)
		: text;
};

const activeStatus = ref([]);
const activePriority = ref([]);
const activeAssignee = ref(null);
const myTasksActive = ref(false);
const dueTodayActive = ref(false);
const overdueActive = ref(false);

const disabledStatuses = ["Template"];

const currentUser = computed(() => {
	return window.frappe?.session?.user || "";
});

onMounted(async () => {
	if (store.taskStatuses.length === 0) {
		await store.fetchTaskStatuses();
	}
	if (store.taskPriorities.length === 0) {
		await store.fetchTaskPriorities();
	}

	if (activeStatus.value.length === 0 && store.taskStatuses.length > 0) {
		activeStatus.value = store.taskStatuses.filter(
			(status) =>
				status !== "Cancelled" &&
				status !== "Closed" &&
				status !== "Completed" &&
				!disabledStatuses.includes(status)
		);
		emitFilters();
	}
});

const priorityColorMap = {
	Urgent: "text-red-500",
	High: "text-orange-400",
	Medium: "text-yellow-500",
	Low: "text-gray-400",
};

const statuses = computed(() => {
	return store.taskStatuses.map((status) => ({
		...getStatusOption(status),
		disabled: disabledStatuses.includes(status),
	}));
});

const priorities = computed(() => {
	return store.taskPriorities.map((priority) => ({
		value: priority,
		label: priority,
		class: priorityColorMap[priority] || "text-gray-400",
	}));
});

const hasActiveFilters = computed(() => {
	return (
		(activeStatus.value && activeStatus.value.length > 0) ||
		(activePriority.value && activePriority.value.length > 0) ||
		activeAssignee.value ||
		myTasksActive.value ||
		dueTodayActive.value ||
		overdueActive.value
	);
});

function toggleStatus(status) {
	if (disabledStatuses.includes(status)) return;
	const index = activeStatus.value.indexOf(status);
	if (index > -1) {
		activeStatus.value.splice(index, 1);
	} else {
		activeStatus.value.push(status);
	}
	emitFilters();
}

function togglePriority(priority) {
	const index = activePriority.value.indexOf(priority);
	if (index > -1) {
		activePriority.value.splice(index, 1);
	} else {
		activePriority.value.push(priority);
	}
	emitFilters();
}

function toggleMyTasks() {
	myTasksActive.value = !myTasksActive.value;
	activeAssignee.value = myTasksActive.value ? currentUser.value : null;
	emitFilters();
}

function toggleDueToday() {
	dueTodayActive.value = !dueTodayActive.value;
	emitFilters();
}

function toggleOverdue() {
	overdueActive.value = !overdueActive.value;
	emitFilters();
}

function clearFilters() {
	activeStatus.value = [];
	activePriority.value = [];
	activeAssignee.value = null;
	myTasksActive.value = false;
	dueTodayActive.value = false;
	overdueActive.value = false;
	emitFilters();
}

function emitFilters() {
	emit("filter-change", {
		status: activeStatus.value,
		priority: activePriority.value,
		assignee: activeAssignee.value,
		dueToday: dueTodayActive.value,
		overdue: overdueActive.value,
	});
}
</script>

<template>
	<div class="px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-start gap-x-6 gap-y-3">

		<!-- Quick -->
		<div class="flex items-center gap-1.5 flex-shrink-0">
			<span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mr-1">
				{{ translate("Quick") }}
			</span>
			<button
				@click="toggleOverdue"
				:class="[
					'flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border transition-colors',
					overdueActive
						? 'bg-red-50 dark:bg-red-900/30 border-red-300 dark:border-red-700 text-red-700 dark:text-red-400'
						: 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
				]"
			>
				<AlertCircle class="w-3 h-3" />
				{{ translate("Przeterminowane") }}
			</button>
			<button
				@click="toggleMyTasks"
				:class="[
					'flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border transition-colors',
					myTasksActive
						? 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-400'
						: 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
				]"
			>
				<User class="w-3 h-3" />
				{{ translate("My Tasks") }}
			</button>
			<button
				@click="toggleDueToday"
				:class="[
					'flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border transition-colors',
					dueTodayActive
						? 'bg-amber-50 dark:bg-amber-900/30 border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-400'
						: 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
				]"
			>
				<Calendar class="w-3 h-3" />
				{{ translate("Due Today") }}
			</button>
		</div>

		<!-- Separator -->
		<div class="hidden sm:block w-px self-stretch bg-gray-200 dark:bg-gray-700"></div>

		<!-- Status -->
		<div class="flex items-center gap-1.5 flex-wrap">
			<span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mr-1">
				{{ translate("Status") }}
			</span>
			<button
				v-for="status in statuses"
				:key="status.value"
				@click="toggleStatus(status.value)"
				:disabled="status.disabled"
				:class="[
					'flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border transition-colors',
					status.disabled ? 'opacity-40 cursor-not-allowed' : '',
					activeStatus.includes(status.value)
						? 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-600 text-blue-700 dark:text-blue-300'
						: 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
				]"
			>
				<component :is="status.icon" :class="['w-3 h-3', status.class]" />
				{{ status.label }}
			</button>
		</div>

		<!-- Separator -->
		<div class="hidden sm:block w-px self-stretch bg-gray-200 dark:bg-gray-700"></div>

		<!-- Priority -->
		<div class="flex items-center gap-1.5 flex-wrap">
			<span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mr-1">
				{{ translate("Priority") }}
			</span>
			<button
				v-for="priority in priorities"
				:key="priority.value"
				@click="togglePriority(priority.value)"
				:class="[
					'flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border transition-colors',
					activePriority.includes(priority.value)
						? 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-600 text-blue-700 dark:text-blue-300'
						: 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
				]"
			>
				<Flag :class="['w-3 h-3', priority.class]" />
				{{ priority.label }}
			</button>
		</div>

		<!-- Clear + Close -->
		<div class="flex items-center gap-2 ml-auto flex-shrink-0">
			<button
				v-if="hasActiveFilters"
				@click="clearFilters"
				class="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
			>
				<X class="w-3 h-3" />
				{{ translate("Clear") }}
			</button>
			<button
				@click="$emit('close')"
				class="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
				:title="translate('Close filters')"
			>
				<X class="w-3.5 h-3.5" />
			</button>
		</div>

	</div>
</template>
