<template>
	<div class="weekly-planner h-full flex flex-col bg-gray-50">
		<!-- Header -->
		<WeeklyPlannerHeader
			@week-change="handleWeekChange"
			@filter-change="handleFilterChange"
			@toggle-resource-pool="store.toggleResourcePool"
			@generate-timesheets="handleGenerateTimesheets"
		/>

		<!-- Main Content -->
		<div class="flex-1 flex overflow-hidden">
			<!-- Task Pool Panel -->
			<TaskPool
				v-if="!store.selectedEmployee"
				:tasks="store.taskPool"
				:loading="store.loading"
				class="w-80 flex-shrink-0 border-r bg-white"
				@dragstart="handleTaskDragStart"
			/>

			<!-- Weekly Grid -->
			<WeeklyPlannerGrid
				:employees="store.filteredEmployees"
				:week-dates="store.weekDates"
				:assignments="store.assignments"
				:capacities="store.capacities"
				:loading="store.loading"
				class="flex-1 overflow-auto"
				@drop="handleDrop"
				@update-hours="handleUpdateHours"
				@delete="handleDelete"
			/>
		</div>

		<!-- Resource Pool Summary (Collapsible) -->
		<ResourcePoolSummary
			v-if="store.showResourcePool"
			:data="store.resourcePoolData"
			@select-employee="handleSelectEmployee"
		/>

		<!-- Hour Allocation Modal -->
		<HourAllocationModal
			v-model:show="showHourModal"
			:task="selectedTask"
			:employee="selectedEmployee"
			:date="selectedDate"
			:current-hours="currentDayHours"
			@confirm="handleHourAllocation"
		/>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useWeeklyPlanningStore } from "../stores/weeklyPlanningStore";
import WeeklyPlannerHeader from "../components/weekly-planner/WeeklyPlannerHeader.vue";
import TaskPool from "../components/weekly-planner/TaskPool.vue";
import WeeklyPlannerGrid from "../components/weekly-planner/WeeklyPlannerGrid.vue";
import ResourcePoolSummary from "../components/weekly-planner/ResourcePoolSummary.vue";
import HourAllocationModal from "../components/weekly-planner/HourAllocationModal.vue";

const router = useRouter();
const store = useWeeklyPlanningStore();

// Modal state
const showHourModal = ref(false);
const selectedTask = ref(null);
const selectedEmployee = ref(null);
const selectedDate = ref(null);
const currentDayHours = ref(0);

// Check Project Manager role on mount
onMounted(() => {
	// Check if user has required roles using frappe.user_roles
	const userRoles = frappe.user_roles || [];
	const hasProjectManagerRole = userRoles.includes("Project Manager");
	const hasProjectsManagerRole = userRoles.includes("Projects Manager");
	const hasSystemManagerRole = userRoles.includes("System Manager");

	if (!hasProjectManagerRole && !hasProjectsManagerRole && !hasSystemManagerRole) {
		frappe.msgprint({
			title: __("Access Denied"),
			message: __(
				"You need Project Manager or Projects Manager role to access Weekly Planner"
			),
			indicator: "red",
		});
		router.push("/project-hub");
		return;
	}

	// Load initial data
	store.fetchWeeklyPlan();
});

function handleWeekChange(direction) {
	store.navigateWeek(direction);
}

function handleFilterChange(filters) {
	if (filters.employee !== undefined) {
		store.setFilter("employee", filters.employee);
	}
	if (filters.projects !== undefined) {
		store.setFilter("projects", filters.projects);
	}
}

function handleTaskDragStart(task) {
	store.draggedTask = task;
}

function handleDrop({ employee, date }) {
	if (!store.draggedTask) return;

	// Open modal with pre-filled data
	selectedTask.value = store.draggedTask;
	selectedEmployee.value = employee;
	selectedDate.value = date;
	currentDayHours.value = store.getHoursForEmployeeAndDate(employee, date);
	showHourModal.value = true;
}

async function handleHourAllocation(hours) {
	try {
		await store.createAssignment(
			selectedEmployee.value,
			selectedDate.value,
			selectedTask.value.name,
			hours
		);

		showHourModal.value = false;
		selectedTask.value = null;
		selectedEmployee.value = null;
		selectedDate.value = null;
		store.draggedTask = null;
	} catch (err) {
		console.error("Failed to allocate hours:", err);
	}
}

async function handleUpdateHours({ assignmentId, hours }) {
	try {
		await store.updateAssignment(assignmentId, hours);
	} catch (err) {
		console.error("Failed to update hours:", err);
	}
}

async function handleDelete(assignmentId) {
	try {
		const confirmed = await new Promise((resolve) => {
			frappe.confirm(
				"Are you sure you want to delete this assignment?",
				() => resolve(true),
				() => resolve(false)
			);
		});

		if (confirmed) {
			await store.deleteAssignment(assignmentId);
		}
	} catch (err) {
		console.error("Failed to delete assignment:", err);
	}
}

function handleSelectEmployee(employee) {
	store.setFilter("employee", employee);
}

async function handleGenerateTimesheets() {
	try {
		const confirmed = await new Promise((resolve) => {
			frappe.confirm(
				"This will create timesheets from all planned assignments for this week. Continue?",
				() => resolve(true),
				() => resolve(false)
			);
		});

		if (confirmed) {
			await store.generateTimesheets();
		}
	} catch (err) {
		console.error("Failed to generate timesheets:", err);
	}
}
</script>
