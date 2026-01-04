<script setup>
import { ref, computed, watch } from "vue";
import { useTaskStore } from "../stores/taskStore";
import {
	Calendar,
	Clock,
	User,
	FileText,
	TrendingUp,
	AlertCircle,
	ChevronDown,
	ChevronUp,
} from "lucide-vue-next";

const props = defineProps({
	project: {
		type: Object,
		required: true,
	},
});

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text) => {
	return typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
		? realWindow.__(text)
		: text;
};

const formatDate = (dateStr) => {
	if (!dateStr) return translate("Not set");
	const date = new Date(dateStr);
	return date.toLocaleDateString("en-US", {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
	});
};

const formatHours = (hours) => {
	if (!hours || hours === 0) return "0h";
	return `${hours.toFixed(1)}h`;
};

const hoursProgress = computed(() => {
	if (!props.project.estimated_hours || props.project.estimated_hours === 0) return 0;
	return Math.min(
		100,
		Math.round((props.project.total_hours / props.project.estimated_hours) * 100)
	);
});

const isOverBudget = computed(() => {
	return (
		props.project.estimated_hours > 0 &&
		props.project.total_hours > props.project.estimated_hours
	);
});

const isOverdue = computed(() => {
	if (!props.project.expected_end_date) return false;
	const endDate = new Date(props.project.expected_end_date);
	const today = new Date();
	return endDate < today && props.project.status !== "Completed";
});

const isExpanded = ref(false);

const store = useTaskStore();
const isSaving = ref(false);

const editableExpectedStart = ref("");
const editableExpectedEnd = ref("");

watch(
	() => props.project,
	(p) => {
		editableExpectedStart.value = p?.expected_start_date || "";
		editableExpectedEnd.value = p?.expected_end_date || "";
	},
	{ immediate: true }
);

const toggleExpand = () => {
	isExpanded.value = !isExpanded.value;
};

async function saveDateField(field, value) {
	isSaving.value = true;
	try {
		await store.updateProject(props.project.name, { [field]: value });
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Project dates saved"),
				indicator: "green",
			});
		}
	} catch (e) {
		editableExpectedStart.value = props.project.expected_start_date || "";
		editableExpectedEnd.value = props.project.expected_end_date || "";
		if (realWindow?.frappe) {
			realWindow.frappe.show_alert({
				message: translate("Could not save project dates"),
				indicator: "red",
			});
		}
	} finally {
		isSaving.value = false;
	}
}
</script>

<template>
	<div class="bg-white border-b border-gray-200">
		<div
			class="px-4 sm:px-6 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50"
			@click="toggleExpand"
		>
			<h3 class="text-sm font-semibold text-gray-700">
				{{ translate("Project Information") }}
			</h3>
			<button class="p-1 rounded hover:bg-gray-200 transition-colors">
				<ChevronUp v-if="isExpanded" class="w-4 h-4 text-gray-500" />
				<ChevronDown v-else class="w-4 h-4 text-gray-500" />
			</button>
		</div>

		<Transition name="expand">
			<div v-if="isExpanded" class="px-4 sm:px-6 pb-4">
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
					<!-- Dates Section -->
					<div class="space-y-2">
						<div class="flex items-start gap-2">
							<Calendar class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
							<div class="flex-1 min-w-0">
								<div class="text-xs text-gray-500">
									{{ translate("Planned Start") }}
								</div>
								<input
									v-model="editableExpectedStart"
									type="date"
									class="mt-1 w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
									@change="
										saveDateField('expected_start_date', editableExpectedStart)
									"
									:disabled="isSaving"
								/>
								<div class="text-xs text-gray-400 mt-0.5">
									{{ formatDate(project.expected_start_date) }}
								</div>
							</div>
						</div>
						<div class="flex items-start gap-2">
							<Calendar class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
							<div class="flex-1 min-w-0">
								<div class="text-xs text-gray-500">
									{{ translate("Planned End") }}
								</div>
								<div
									class="text-sm font-medium"
									:class="isOverdue ? 'text-red-600' : 'text-gray-900'"
								>
									<input
										v-model="editableExpectedEnd"
										type="date"
										class="mt-1 w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
										@change="
											saveDateField('expected_end_date', editableExpectedEnd)
										"
										:disabled="isSaving"
									/>
									<div class="text-xs text-gray-400 mt-0.5">
										{{ formatDate(project.expected_end_date) }}
										<span v-if="isOverdue" class="ml-1 text-xs">{{
											translate("(Overdue)")
										}}</span>
									</div>
								</div>
							</div>
						</div>
					</div>

					<!-- Actual Dates Section -->
					<div class="space-y-2">
						<div class="flex items-start gap-2">
							<Calendar class="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
							<div class="flex-1 min-w-0">
								<div class="text-xs text-gray-500">Actual Start</div>
								<div class="text-sm font-medium text-gray-900">
									{{ formatDate(project.actual_start_date) }}
								</div>
							</div>
						</div>
						<div class="flex items-start gap-2">
							<Calendar class="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
							<div class="flex-1 min-w-0">
								<div class="text-xs text-gray-500">Actual End</div>
								<div class="text-sm font-medium text-gray-900">
									{{ formatDate(project.actual_end_date) }}
								</div>
							</div>
						</div>
					</div>

					<!-- Hours Section -->
					<div class="space-y-2">
						<div class="flex items-start gap-2">
							<Clock class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
							<div class="flex-1 min-w-0">
								<div class="text-xs text-gray-500">Estimated Hours</div>
								<div class="text-sm font-medium text-gray-900">
									{{ formatHours(project.estimated_hours) }}
								</div>
							</div>
						</div>
						<div class="flex items-start gap-2">
							<TrendingUp
								class="w-4 h-4 mt-0.5 flex-shrink-0"
								:class="isOverBudget ? 'text-red-500' : 'text-green-500'"
							/>
							<div class="flex-1 min-w-0">
								<div class="text-xs text-gray-500">Logged Hours</div>
								<div
									class="text-sm font-medium"
									:class="isOverBudget ? 'text-red-600' : 'text-gray-900'"
								>
									{{ formatHours(project.total_hours) }}
									<span
										v-if="project.estimated_hours > 0"
										class="text-xs text-gray-500 ml-1"
									>
										({{ hoursProgress }}%)
									</span>
								</div>
							</div>
						</div>
						<!-- Hours progress bar -->
						<div v-if="project.estimated_hours > 0" class="mt-2">
							<div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
								<div
									class="h-full rounded-full transition-all duration-300"
									:class="isOverBudget ? 'bg-red-500' : 'bg-green-500'"
									:style="{ width: Math.min(100, hoursProgress) + '%' }"
								></div>
							</div>
						</div>
					</div>

					<!-- Customer Section -->
					<div class="space-y-2">
						<div class="flex items-start gap-2">
							<User class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
							<div class="flex-1 min-w-0">
								<div class="text-xs text-gray-500">Customer</div>
								<div
									class="text-sm font-medium text-gray-900 truncate"
									:title="project.customer_name || project.customer"
								>
									{{
										project.customer_name || project.customer || "Not assigned"
									}}
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Notes Section (full width if present) -->
				<div v-if="project.notes" class="mt-4 pt-4 border-t border-gray-100">
					<div class="flex items-start gap-2">
						<FileText class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
						<div class="flex-1 min-w-0">
							<div class="text-xs text-gray-500 mb-1">Notes</div>
							<div class="text-sm text-gray-700 whitespace-pre-wrap">
								{{ project.notes }}
							</div>
						</div>
					</div>
				</div>

				<!-- Warnings -->
				<div v-if="isOverdue || isOverBudget" class="mt-4 pt-4 border-t border-gray-100">
					<div class="flex items-start gap-2 text-amber-600">
						<AlertCircle class="w-4 h-4 mt-0.5 flex-shrink-0" />
						<div class="text-sm">
							<span v-if="isOverdue">Project is overdue. </span>
							<span v-if="isOverBudget"
								>Hours budget exceeded by
								{{
									formatHours(project.total_hours - project.estimated_hours)
								}}.</span
							>
						</div>
					</div>
				</div>
			</div>
		</Transition>
	</div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
	transition: all 0.3s ease;
	overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
	max-height: 0;
	opacity: 0;
}

.expand-enter-to,
.expand-leave-from {
	max-height: 500px;
	opacity: 1;
}
</style>
