<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useTaskStore } from "../stores/taskStore";
import {
	Diamond,
	Plus,
	Calendar,
	MoreVertical,
	Edit2,
	Trash2,
	X,
	Search,
	CheckCircle2,
	GripVertical,
} from "lucide-vue-next";
import MilestoneModal from "./MilestoneModal.vue";
import { translate } from "../utils/translation";

const emit = defineEmits(["close"]);

const store = useTaskStore();
const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;

// Modal state
const showCreateModal = ref(false);
const showEditModal = ref(false);
const editingMilestone = ref(null);
const openMenuId = ref(null);

// Inline filter state
const search = ref("");
const includeDone = ref(false);
const sortBy = computed({
	get: () => store.milestoneSortBy,
	set: (val) => { store.milestoneSortBy = val; },
});

// Drag & drop (task assignment)
const dragOverMilestone = ref(null);

// Milestone reorder drag state
const draggingMilestoneName = ref(null);
const reorderDropIndex = ref(null);

// Filtered + sorted milestones
const visibleMilestones = computed(() => {
	const query = search.value.trim().toLowerCase();
	let list = [...store.milestones];

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
	} else if (sortBy.value === "deadline") {
		list.sort((a, b) => {
			const aDate = a.milestone_date ? new Date(a.milestone_date).getTime() : Number.POSITIVE_INFINITY;
			const bDate = b.milestone_date ? new Date(b.milestone_date).getTime() : Number.POSITIVE_INFINITY;
			return aDate - bDate;
		});
	} else {
		// manual
		list.sort((a, b) => {
			if (a.sort_order != null && b.sort_order != null) return a.sort_order - b.sort_order;
			if (a.sort_order != null) return -1;
			if (b.sort_order != null) return 1;
			const aDate = a.milestone_date ? new Date(a.milestone_date).getTime() : Number.POSITIVE_INFINITY;
			const bDate = b.milestone_date ? new Date(b.milestone_date).getTime() : Number.POSITIVE_INFINITY;
			return aDate - bDate;
		});
	}
	return list;
});

const activeMilestoneNames = computed(() => new Set(store.activeMilestoneFilter));

// Preset filter actions
function setPresetAll() {
	store.setMilestoneFilter(visibleMilestones.value.map((m) => m.name));
}
function setPresetActive() {
	store.setMilestoneFilter(
		store.milestones.filter((m) => m.health !== "completed" && m.health !== "cancelled").map((m) => m.name)
	);
}
function setPresetOverdue() {
	store.setMilestoneFilter(store.milestones.filter((m) => m.health === "overdue").map((m) => m.name));
}
function setPresetNoDeadline() {
	store.setMilestoneFilter(store.milestones.filter((m) => !m.milestone_date).map((m) => m.name));
}

// Menu handlers
function toggleMenu(milestoneName, event) {
	event.stopPropagation();
	openMenuId.value = openMenuId.value === milestoneName ? null : milestoneName;
}

function handleEdit(milestone, event) {
	event.stopPropagation();
	editingMilestone.value = milestone;
	showEditModal.value = true;
	openMenuId.value = null;
}

async function handleDelete(milestone, event) {
	event.stopPropagation();
	openMenuId.value = null;
	if (
		!confirm(
			translate(`Delete milestone "${milestone.milestone_name}"? Tasks will be detached but not deleted.`)
		)
	) {
		return;
	}
	try {
		await store.deleteMilestone(milestone.name);
		realWindow?.frappe?.show_alert({ message: translate("Milestone deleted"), indicator: "green" });
	} catch {
		realWindow?.frappe?.show_alert({ message: translate("Failed to delete milestone"), indicator: "red" });
	}
}

async function handleCreate(data) {
	try {
		await store.createMilestone({ ...data, project: store.project.name });
		showCreateModal.value = false;
		realWindow?.frappe?.show_alert({ message: translate("Milestone created"), indicator: "green" });
	} catch {
		realWindow?.frappe?.show_alert({ message: translate("Failed to create milestone"), indicator: "red" });
	}
}

async function handleUpdate(data) {
	try {
		await store.updateMilestone(editingMilestone.value.name, data);
		showEditModal.value = false;
		editingMilestone.value = null;
		realWindow?.frappe?.show_alert({ message: translate("Milestone updated"), indicator: "green" });
	} catch {
		realWindow?.frappe?.show_alert({ message: translate("Failed to update milestone"), indicator: "red" });
	}
}

// Drag & drop helpers
function handleMilestoneDragStart(event, milestoneName) {
	draggingMilestoneName.value = milestoneName;
	event.dataTransfer.setData("application/x-milestone-reorder", milestoneName);
	// Clear text/plain so browser text content isn't passed as a task name
	event.dataTransfer.setData("text/plain", "");
	event.dataTransfer.effectAllowed = "move";
}

function handleMilestoneDragEnd() {
	draggingMilestoneName.value = null;
	reorderDropIndex.value = null;
}

function isMilestoneReorderDrag(event) {
	return (
		draggingMilestoneName.value ||
		event.dataTransfer.types.includes("application/x-milestone-reorder")
	);
}

function handleDragOver(event, milestoneName, index) {
	event.preventDefault();
	if (isMilestoneReorderDrag(event)) {
		event.dataTransfer.dropEffect = "move";
		reorderDropIndex.value = index;
		dragOverMilestone.value = null;
	} else {
		event.dataTransfer.dropEffect = "move";
		dragOverMilestone.value = milestoneName;
		reorderDropIndex.value = null;
	}
}

function handleDragLeave(event, milestoneName) {
	if (event.currentTarget.contains(event.relatedTarget)) return;
	if (dragOverMilestone.value === milestoneName) dragOverMilestone.value = null;
	reorderDropIndex.value = null;
}

async function handleDrop(event, milestoneName, index) {
	event.preventDefault();

	const draggedMilestoneName =
		draggingMilestoneName.value ||
		event.dataTransfer.getData("application/x-milestone-reorder") ||
		null;

	if (draggedMilestoneName) {
		const draggedName = draggedMilestoneName;
		draggingMilestoneName.value = null;
		reorderDropIndex.value = null;

		const list = [...visibleMilestones.value];
		const fromIdx = list.findIndex((m) => m.name === draggedName);
		if (fromIdx !== -1 && fromIdx !== index) {
			const [removed] = list.splice(fromIdx, 1);
			list.splice(index, 0, removed);
			try {
				await store.reorderMilestones(list.map((m) => m.name));
			} catch {
				realWindow?.frappe?.show_alert({
					message: translate("Failed to reorder milestones"),
					indicator: "red",
				});
			}
		}
		return;
	}

	dragOverMilestone.value = null;
	const taskName = event.dataTransfer.getData("text/plain");
	if (!taskName) return;
	try {
		await store.assignTaskToMilestone(taskName, milestoneName);
		realWindow?.frappe?.show_alert({ message: translate("Task assigned to milestone"), indicator: "green" });
	} catch {
		realWindow?.frappe?.show_alert({ message: translate("Failed to assign task"), indicator: "red" });
	}
}

// Helpers
function getBorderColor(milestone) {
	if (milestone.color) return milestone.color;
	const healthColors = {
		completed: "#10b981",
		on_track: "#3b82f6",
		at_risk: "#f59e0b",
		overdue: "#ef4444",
		no_deadline: "#9ca3af",
		cancelled: "#6b7280",
	};
	return healthColors[milestone.health] || "#3b82f6";
}

function getHealthColor(health) {
	const colors = {
		completed: "bg-green-100 text-green-700 border-green-200",
		on_track: "bg-blue-100 text-blue-700 border-blue-200",
		at_risk: "bg-orange-100 text-orange-700 border-orange-200",
		overdue: "bg-red-100 text-red-700 border-red-200",
		no_deadline: "bg-gray-100 text-gray-600 border-gray-200",
		cancelled: "bg-gray-100 text-gray-500 border-gray-200",
	};
	return colors[health] || colors.no_deadline;
}

function getHealthLabel(health) {
	const labels = {
		completed: translate("Completed"),
		on_track: translate("On Track"),
		at_risk: translate("At Risk"),
		overdue: translate("Overdue"),
		no_deadline: translate("No Deadline"),
		cancelled: translate("Cancelled"),
	};
	return labels[health] || health;
}

function formatDate(dateStr) {
	if (!dateStr) return translate("No deadline");
	const date = new Date(dateStr);
	return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function handleClickOutside(event) {
	if (openMenuId.value && !event.target.closest(".milestone-menu")) {
		openMenuId.value = null;
	}
}

onMounted(() => document.addEventListener("click", handleClickOutside));
onUnmounted(() => document.removeEventListener("click", handleClickOutside));
</script>

<template>
	<div class="flex flex-col h-full bg-white dark:bg-gray-800 w-72 border-r border-gray-200 dark:border-gray-700 flex-shrink-0">
		<!-- Header -->
		<div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
			<div class="flex items-center gap-2">
				<Diamond class="w-4 h-4 text-purple-600 dark:text-purple-400" />
				<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
					{{ translate("Milestones") }}
				</h3>
				<span class="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
					{{ store.milestones.length }}
				</span>
			</div>
			<div class="flex items-center gap-1">
				<button
					@click="showCreateModal = true"
					class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-purple-600 dark:text-purple-400"
					:title="translate('Add milestone')"
				>
					<Plus class="w-4 h-4" />
				</button>
				<button
					@click="emit('close')"
					class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400"
					:title="translate('Close')"
				>
					<X class="w-4 h-4" />
				</button>
			</div>
		</div>

		<!-- Filter controls -->
		<div class="px-3 pt-3 pb-2 space-y-2 flex-shrink-0 border-b border-gray-100 dark:border-gray-700">
			<!-- Search -->
			<div class="relative">
				<Search class="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
				<input
					v-model="search"
					type="text"
					:placeholder="translate('Search milestone...')"
					class="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-1 focus:ring-purple-500 focus:border-purple-500"
				/>
			</div>

			<!-- Sort + Show done -->
			<div class="flex gap-2">
				<select
					v-model="sortBy"
					class="flex-1 min-w-0 pl-2 pr-6 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300"
				>
					<option value="manual">{{ translate("Sort: manual") }}</option>
					<option value="deadline">{{ translate("Sort: deadline") }}</option>
					<option value="name">{{ translate("Sort: name") }}</option>
					<option value="progress">{{ translate("Sort: progress") }}</option>
				</select>
				<button
					type="button"
					@click="includeDone = !includeDone"
					:class="[
						'px-2 py-1.5 text-xs rounded-lg border transition-colors whitespace-nowrap',
						includeDone
							? 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300'
							: 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700',
					]"
				>
					{{ includeDone ? translate("Hide done") : translate("Show done") }}
				</button>
			</div>

			<!-- Preset chips -->
			<div class="flex flex-wrap gap-1">
				<button
					type="button"
					@click="setPresetAll"
					class="text-[11px] px-2 py-0.5 rounded-full border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
				>
					{{ translate("All") }}
				</button>
				<button
					type="button"
					@click="setPresetActive"
					class="text-[11px] px-2 py-0.5 rounded-full border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
				>
					{{ translate("Active") }}
				</button>
				<button
					type="button"
					@click="setPresetOverdue"
					class="text-[11px] px-2 py-0.5 rounded-full border border-red-200 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400"
				>
					{{ translate("Overdue") }}
				</button>
				<button
					type="button"
					@click="setPresetNoDeadline"
					class="text-[11px] px-2 py-0.5 rounded-full border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
				>
					{{ translate("No deadline") }}
				</button>
				<button
					v-if="store.activeMilestoneFilter.length"
					type="button"
					@click="store.clearMilestoneFilter()"
					class="text-[11px] px-2 py-0.5 rounded-full border border-purple-200 dark:border-purple-700 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 flex items-center gap-1"
				>
					<X class="w-2.5 h-2.5" />
					{{ translate("Clear") }} ({{ store.activeMilestoneFilter.length }})
				</button>
			</div>
		</div>

		<!-- Milestone list -->
		<div class="flex-1 overflow-y-auto p-2 space-y-2">
			<div
				v-for="(milestone, index) in visibleMilestones"
				:key="milestone.name"
				:draggable="sortBy === 'manual'"
				@dragstart="sortBy === 'manual' && handleMilestoneDragStart($event, milestone.name)"
				@dragend="handleMilestoneDragEnd"
				@dragover="handleDragOver($event, milestone.name, index)"
				@dragleave="handleDragLeave($event, milestone.name)"
				@drop="handleDrop($event, milestone.name, index)"
				@click="store.toggleMilestoneFilter(milestone.name)"
				:class="[
					'p-3 rounded-lg border-2 transition-all relative cursor-pointer',
					draggingMilestoneName === milestone.name
						? 'opacity-40'
						: reorderDropIndex === index && draggingMilestoneName !== milestone.name && sortBy === 'manual'
						? 'border-purple-400 bg-purple-50 dark:bg-purple-900/20 shadow-md'
						: activeMilestoneNames.has(milestone.name)
						? 'border-purple-400 bg-purple-50 dark:bg-purple-900/20 shadow-sm'
						: dragOverMilestone === milestone.name
						? 'border-purple-300 bg-purple-50 dark:bg-purple-900/20 shadow-md'
						: 'border-transparent hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-200 dark:hover:border-gray-600',
				]"
				:style="{ borderLeftColor: getBorderColor(milestone), borderLeftWidth: '4px' }"
			>
				<!-- Header row -->
				<div class="flex items-start justify-between mb-2">
					<div class="flex items-center gap-1.5 flex-1 min-w-0">
						<!-- Drag handle (manual sort only) -->
						<GripVertical
							v-if="sortBy === 'manual'"
							class="w-3.5 h-3.5 text-gray-300 dark:text-gray-600 flex-shrink-0 cursor-grab active:cursor-grabbing"
							@click.stop
						/>
						<!-- Active filter checkmark -->
						<CheckCircle2
							v-else-if="activeMilestoneNames.has(milestone.name)"
							class="w-3.5 h-3.5 text-purple-600 dark:text-purple-400 flex-shrink-0"
						/>
						<span class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
							{{ milestone.milestone_name }}
						</span>
					</div>
					<div class="milestone-menu relative flex-shrink-0" @click.stop>
						<button
							@click="toggleMenu(milestone.name, $event)"
							class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
						>
							<MoreVertical class="w-3 h-3 text-gray-500 dark:text-gray-400" />
						</button>
						<Transition name="menu-fade">
							<div
								v-if="openMenuId === milestone.name"
								class="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-700 rounded-md shadow-lg border border-gray-200 dark:border-gray-600 z-20 py-1"
							>
								<button
									@click="handleEdit(milestone, $event)"
									class="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 flex items-center gap-2"
								>
									<Edit2 class="w-3 h-3" />
									{{ translate("Edit") }}
								</button>
								<button
									@click="handleDelete(milestone, $event)"
									class="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-600 text-red-600 dark:text-red-400 flex items-center gap-2"
								>
									<Trash2 class="w-3 h-3" />
									{{ translate("Delete") }}
								</button>
							</div>
						</Transition>
					</div>
				</div>

				<!-- Progress bar -->
				<div class="mb-2">
					<div class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
						<div
							class="h-full transition-all duration-300"
							:style="{
								width: `${milestone.progress || 0}%`,
								backgroundColor: getBorderColor(milestone),
							}"
						/>
					</div>
					<div class="flex items-center justify-between mt-1">
						<span class="text-xs text-gray-600 dark:text-gray-400">{{ milestone.progress || 0 }}%</span>
						<span class="text-xs text-gray-500 dark:text-gray-400">
							{{ milestone.completed_tasks || 0 }}/{{ milestone.total_tasks || 0 }}
							{{ translate("tasks") }}
						</span>
					</div>
				</div>

				<!-- Date & health -->
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
						<Calendar class="w-3 h-3" />
						<span>{{ formatDate(milestone.milestone_date) }}</span>
					</div>
					<span :class="['px-2 py-0.5 rounded-full text-xs font-medium border', getHealthColor(milestone.health)]">
						{{ getHealthLabel(milestone.health) }}
					</span>
				</div>

				<!-- Drag & drop hint -->
				<div
					v-if="dragOverMilestone === milestone.name"
					class="absolute inset-0 rounded-lg border-2 border-dashed border-purple-400 bg-purple-50/80 dark:bg-purple-900/40 flex items-center justify-center pointer-events-none"
				>
					<span class="text-xs font-medium text-purple-700 dark:text-purple-300">
						{{ translate("Drop to assign") }}
					</span>
				</div>
			</div>

			<!-- Empty state -->
			<div v-if="visibleMilestones.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
				<Diamond class="w-8 h-8 mx-auto mb-2 opacity-30" />
				<p class="text-sm">{{ translate("No milestones") }}</p>
				<button
					@click="showCreateModal = true"
					class="text-xs text-purple-600 dark:text-purple-400 hover:underline mt-1"
				>
					{{ translate("Create first milestone") }}
				</button>
			</div>
		</div>

		<!-- Modals -->
		<MilestoneModal :show="showCreateModal" @save="handleCreate" @close="showCreateModal = false" />
		<MilestoneModal
			:show="showEditModal"
			:milestone="editingMilestone"
			edit-mode
			@save="handleUpdate"
			@close="showEditModal = false; editingMilestone = null;"
		/>
	</div>
</template>

<style scoped>
.menu-fade-enter-active,
.menu-fade-leave-active {
	transition: opacity 0.15s ease, transform 0.15s ease;
}
.menu-fade-enter-from,
.menu-fade-leave-to {
	opacity: 0;
	transform: scale(0.95);
}
</style>
