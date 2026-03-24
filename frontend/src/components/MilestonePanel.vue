<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useTaskStore } from "../stores/taskStore";
import {
	Diamond,
	Plus,
	Calendar,
	Filter,
	MoreVertical,
	Edit2,
	Trash2,
	X,
	ChevronDown,
	ChevronUp,
	GripVertical,
} from "lucide-vue-next";
import MilestoneModal from "./MilestoneModal.vue";
import MilestoneFilterModal from "./MilestoneFilterModal.vue";

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text) => {
	return typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
		? realWindow.__(text)
		: text;
};

const store = useTaskStore();
const showCreateModal = ref(false);
const showEditModal = ref(false);
const showFilterModal = ref(false);
const editingMilestone = ref(null);
const openMenuId = ref(null);
const isCollapsed = ref(false);

// Load milestones when project changes
watch(
	() => store.project?.name,
	(projectName) => {
		if (projectName) {
			store.fetchMilestones(projectName);
		}
	},
	{ immediate: true }
);

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
			translate(
				`Delete milestone "${milestone.milestone_name}"? Tasks will be detached but not deleted.`
			)
		)
	) {
		return;
	}

	try {
		await store.deleteMilestone(milestone.name);
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Milestone deleted"),
				indicator: "green",
			});
		}
	} catch (error) {
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Failed to delete milestone"),
				indicator: "red",
			});
		}
	}
}

async function handleCreate(data) {
	try {
		await store.createMilestone({
			...data,
			project: store.project.name,
		});
		showCreateModal.value = false;
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Milestone created"),
				indicator: "green",
			});
		}
	} catch (error) {
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Failed to create milestone"),
				indicator: "red",
			});
		}
	}
}

async function handleUpdate(data) {
	try {
		await store.updateMilestone(editingMilestone.value.name, data);
		showEditModal.value = false;
		editingMilestone.value = null;
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Milestone updated"),
				indicator: "green",
			});
		}
	} catch (error) {
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Failed to update milestone"),
				indicator: "red",
			});
		}
	}
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

function getBorderColor(milestone) {
	if (milestone.color) {
		return milestone.color;
	}
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

function formatDate(dateStr) {
	if (!dateStr) return "No deadline";
	const date = new Date(dateStr);
	return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

const activeMilestoneNames = computed(() => new Set(store.activeMilestoneFilter));

const activeMilestoneLabels = computed(() => {
	const byName = new Map(store.milestones.map((m) => [m.name, m]));
	return store.activeMilestoneFilter
		.map((name) => byName.get(name)?.milestone_name || name)
		.filter(Boolean);
});

const milestonesSorted = computed(() => {
	return [...store.milestones].sort((a, b) => {
		if (a.sort_order != null && b.sort_order != null) return a.sort_order - b.sort_order;
		if (a.sort_order != null) return -1;
		if (b.sort_order != null) return 1;
		const aDate = a.milestone_date ? new Date(a.milestone_date).getTime() : Number.POSITIVE_INFINITY;
		const bDate = b.milestone_date ? new Date(b.milestone_date).getTime() : Number.POSITIVE_INFINITY;
		return aDate - bDate;
	});
});

function applyMilestoneFilters(selectedMilestones) {
	store.setMilestoneFilter(selectedMilestones);
}

// Close menu when clicking outside
function handleClickOutside(event) {
	if (openMenuId.value && !event.target.closest(".milestone-menu")) {
		openMenuId.value = null;
	}
}

// Drag & Drop handlers
const dragOverMilestone = ref(null);

// Milestone reorder drag state
const draggingMilestoneName = ref(null);
const reorderDropIndex = ref(null);

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

function handleDragOver(event, milestoneName, index) {
	event.preventDefault();
	if (draggingMilestoneName.value) {
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

	if (draggingMilestoneName.value) {
		const draggedName = draggingMilestoneName.value;
		draggingMilestoneName.value = null;
		reorderDropIndex.value = null;

		const list = [...milestonesSorted.value];
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

	const task = store.tasks.find((t) => t.name === taskName);
	if (!task) return;

	try {
		await store.assignTaskToMilestone(taskName, milestoneName);
		realWindow?.frappe?.show_alert({
			message: translate("Task assigned to milestone"),
			indicator: "green",
		});
	} catch {
		realWindow?.frappe?.show_alert({
			message: translate("Failed to assign task"),
			indicator: "red",
		});
	}
}

onMounted(() => {
	document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
	document.removeEventListener("click", handleClickOutside);
});
</script>

<template>
	<div class="milestone-panel bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
		<!-- Header -->
		<div
			class="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
			@click="isCollapsed = !isCollapsed"
		>
			<div class="flex items-center gap-2">
				<Diamond class="w-4 h-4 text-blue-600 dark:text-blue-400" />
				<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
					{{ translate("Milestones") }}
				</h3>
				<span class="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
					{{ store.milestones.length }}
				</span>
			</div>
			<div class="flex items-center gap-2">
				<button
					@click.stop="showFilterModal = true"
					class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 relative"
					:title="translate('Filter milestones')"
				>
					<Filter class="w-4 h-4" />
					<span
						v-if="store.activeMilestoneFilter.length"
						class="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-blue-600"
					/>
				</button>
				<button
					@click.stop="showCreateModal = true"
					class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-blue-600 dark:text-blue-400"
					:title="translate('Add milestone')"
				>
					<Plus class="w-4 h-4" />
				</button>
				<component
					:is="isCollapsed ? ChevronDown : ChevronUp"
					class="w-4 h-4 text-gray-400"
				/>
			</div>
		</div>

		<!-- Active Filter Indicator -->
		<div
			v-if="store.activeMilestoneFilter.length && !isCollapsed"
			class="px-4 py-2 bg-blue-50 dark:bg-blue-900/30 border-b border-blue-100 dark:border-blue-800 flex items-center justify-between"
		>
			<div class="min-w-0">
				<span class="text-xs text-blue-700 dark:text-blue-400 block">
					{{ translate("Filtering by milestone") }}
				</span>
				<div class="flex gap-1 mt-1 flex-wrap">
					<span
						v-for="label in activeMilestoneLabels"
						:key="label"
						class="text-[11px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-800 dark:text-blue-200 max-w-[140px] truncate"
						:title="label"
					>
						{{ label }}
					</span>
				</div>
			</div>
			<button
				@click="store.clearMilestoneFilter()"
				class="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 flex items-center gap-1"
			>
				<X class="w-3 h-3" />
				{{ translate("Clear") }}
			</button>
		</div>

		<!-- Milestone List -->
		<div v-if="!isCollapsed" class="p-2 space-y-2 max-h-64 overflow-y-auto">
			<div
				v-for="(milestone, index) in milestonesSorted"
				:key="milestone.name"
				draggable="true"
				@dragstart="handleMilestoneDragStart($event, milestone.name)"
				@dragend="handleMilestoneDragEnd"
				@dragover="handleDragOver($event, milestone.name, index)"
				@dragleave="handleDragLeave($event, milestone.name)"
				@drop="handleDrop($event, milestone.name, index)"
				:class="[
					'p-3 rounded-lg border-2 transition-all relative',
					draggingMilestoneName === milestone.name
						? 'opacity-40'
						: reorderDropIndex === index && draggingMilestoneName !== milestone.name
						? 'border-blue-400 bg-blue-50 dark:bg-blue-900/30 shadow-md'
						: activeMilestoneNames.has(milestone.name)
						? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 shadow-sm'
						: dragOverMilestone === milestone.name
						? 'border-blue-400 bg-blue-50 dark:bg-blue-900/30 shadow-md scale-102'
						: 'border-transparent hover:bg-gray-50 dark:hover:bg-gray-700',
				]"
				:style="{ borderLeftColor: getBorderColor(milestone), borderLeftWidth: '4px' }"
			>
				<!-- Header Row -->
				<div class="flex items-start justify-between mb-2">
					<div class="flex items-center gap-2 flex-1 min-w-0">
						<GripVertical class="w-3 h-3 text-gray-300 dark:text-gray-600 flex-shrink-0 cursor-grab active:cursor-grabbing" />
						<span class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
							{{ milestone.milestone_name }}
						</span>
					</div>
					<div class="milestone-menu relative">
						<button
							@click="toggleMenu(milestone.name, $event)"
							class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
						>
							<MoreVertical class="w-3 h-3 text-gray-500 dark:text-gray-400" />
						</button>

						<!-- Context Menu -->
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

				<!-- Progress Bar -->
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
						<span class="text-xs text-gray-600 dark:text-gray-400"> {{ milestone.progress || 0 }}% </span>
						<span class="text-xs text-gray-500 dark:text-gray-400">
							{{ milestone.completed_tasks || 0 }}/{{ milestone.total_tasks || 0 }}
							{{ translate("tasks") }}
						</span>
					</div>
				</div>

				<!-- Date & Health -->
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
						<Calendar class="w-3 h-3" />
						<span>{{ formatDate(milestone.milestone_date) }}</span>
					</div>
					<span
						:class="[
							'px-2 py-0.5 rounded-full text-xs font-medium border',
							getHealthColor(milestone.health),
						]"
					>
						{{ getHealthLabel(milestone.health) }}
					</span>
				</div>
			</div>

			<!-- Empty State -->
			<div v-if="milestonesSorted.length === 0" class="text-center py-6 text-gray-500 dark:text-gray-400">
				<Diamond class="w-8 h-8 mx-auto mb-2 opacity-30" />
				<p class="text-sm">{{ translate("No milestones") }}</p>
				<button
					@click="showCreateModal = true"
					class="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-1"
				>
					{{ translate("Create first milestone") }}
				</button>
			</div>
		</div>

		<!-- Modals -->
		<MilestoneModal
			:show="showCreateModal"
			@save="handleCreate"
			@close="showCreateModal = false"
		/>

		<MilestoneModal
			:show="showEditModal"
			:milestone="editingMilestone"
			edit-mode
			@save="handleUpdate"
			@close="
				showEditModal = false;
				editingMilestone = null;
			"
		/>

		<MilestoneFilterModal
			:show="showFilterModal"
			:milestones="store.milestones"
			:selected-milestones="store.activeMilestoneFilter"
			@close="showFilterModal = false"
			@apply="applyMilestoneFilters"
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
