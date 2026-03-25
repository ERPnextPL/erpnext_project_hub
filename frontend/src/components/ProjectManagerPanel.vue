<script setup>
import { ref, computed, watch } from "vue";
import {
	TrendingUp,
	TrendingDown,
	Clock,
	Users,
	ChevronDown,
	ChevronUp,
	AlertTriangle,
	CheckCircle2,
	FileEdit,
} from "lucide-vue-next";
import { translate } from "../utils/translation";

const props = defineProps({
	project: {
		type: Object,
		required: true,
	},
});

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;

function getCsrfToken() {
	if (realWindow?.frappe?.csrf_token && realWindow.frappe.csrf_token !== "None") {
		return realWindow.frappe.csrf_token;
	}
	if (realWindow?.csrf_token && realWindow.csrf_token !== "{{ csrf_token }}") {
		return realWindow.csrf_token;
	}
	return "";
}

async function apiCall(method, params = {}) {
	const formData = new FormData();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined) {
			formData.append(key, value);
		}
	});
	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: { "X-Frappe-CSRF-Token": getCsrfToken() },
		body: formData,
	});
	const data = await response.json();
	if (!response.ok) throw new Error(data.exception || "API Error");
	return data.message;
}

const isExpanded = ref(false);
const loading = ref(false);
const financials = ref(null);
const error = ref(null);


async function loadFinancials() {
	if (financials.value) return; // already loaded
	loading.value = true;
	error.value = null;
	try {
		financials.value = await apiCall(
			"erpnext_projekt_hub.api.project_hub.get_project_financials",
			{ project: props.project.name }
		);
	} catch (e) {
		error.value = translate("Could not load financial data.");
	} finally {
		loading.value = false;
	}
}

async function toggleExpand() {
	isExpanded.value = !isExpanded.value;
	if (isExpanded.value && !financials.value) {
		await loadFinancials();
	}
}

// Reload when project changes
watch(
	() => props.project.name,
	() => {
		financials.value = null;
		if (isExpanded.value) loadFinancials();
	}
);

// ── Computed helpers ──────────────────────────────────────────────────────────

const currency = computed(() => realWindow?.frappe?.boot?.sysdefaults?.currency || "PLN");

function formatCurrency(value) {
	if (!value && value !== 0) return "—";
	return new Intl.NumberFormat("pl-PL", {
		style: "currency",
		currency: currency.value,
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	}).format(value);
}

function formatHours(h) {
	if (!h && h !== 0) return "—";
	return `${Number(h).toFixed(1)} h`;
}

const hasFinancialData = computed(() => {
	if (!financials.value) return false;
	return (
		financials.value.estimated_costing > 0 ||
		financials.value.total_sales_amount > 0 ||
		financials.value.gross_margin !== 0
	);
});

const hoursProgress = computed(() => {
	if (!financials.value || !financials.value.estimated_hours) return 0;
	return Math.min(100, Math.round((financials.value.total_hours / financials.value.estimated_hours) * 100));
});

const hoursOverBudget = computed(() => {
	if (!financials.value || !financials.value.estimated_hours) return false;
	return financials.value.total_hours > financials.value.estimated_hours;
});

const marginStatus = computed(() => {
	if (!financials.value) return null;
	const pct = financials.value.per_gross_margin;
	if (pct === 0 && financials.value.gross_margin === 0) return null;
	if (pct >= 20) return "good";
	if (pct >= 0) return "warn";
	return "bad";
});

const budgetMarginStatus = computed(() => {
	if (!financials.value || !financials.value.estimated_costing) return null;
	const pct = financials.value.per_budget_margin;
	if (pct >= 30) return "good";
	if (pct >= 0) return "warn";
	return "bad";
});

const budgetUtilization = computed(() => {
	if (!financials.value || !financials.value.estimated_costing) return 0;
	return (financials.value.total_current_cost / financials.value.estimated_costing) * 100;
});

const budgetSegments = computed(() => {
	if (!financials.value || !financials.value.estimated_costing) return { timesheets: 0, purchase: 0, materials: 0 };
	const budget = financials.value.estimated_costing;
	const timesheets = Math.min(100, (financials.value.total_costing_amount / budget) * 100);
	const purchase = Math.min(100 - timesheets, (financials.value.total_purchase_cost / budget) * 100);
	const materials = Math.min(100 - timesheets - purchase, (financials.value.total_consumed_material_cost / budget) * 100);
	return { timesheets, purchase, materials };
});

const showBudgetTooltip = ref(false);
</script>

<template>
	<div
		v-if="project.is_manager"
		class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700"
	>
		<!-- Header row -->
		<div
			class="px-4 sm:px-6 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
			@click="toggleExpand"
		>
			<div class="flex items-center gap-2">
				<TrendingUp class="w-4 h-4 text-indigo-500" />
				<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
					{{ translate("Manager Summary") }}
				</h3>
			</div>
			<button class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
				<ChevronUp v-if="isExpanded" class="w-4 h-4 text-gray-500 dark:text-gray-400" />
				<ChevronDown v-else class="w-4 h-4 text-gray-500 dark:text-gray-400" />
			</button>
		</div>

		<Transition name="expand">
			<div v-if="isExpanded" class="px-4 sm:px-6 pb-5">
				<!-- Loading -->
				<div v-if="loading" class="py-6 flex justify-center">
					<div class="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
				</div>

				<!-- Error -->
				<div v-else-if="error" class="py-4 text-sm text-red-600 flex items-center gap-2">
					<AlertTriangle class="w-4 h-4 flex-shrink-0" />
					{{ error }}
				</div>

				<template v-else-if="financials">
					<!-- ── Grid KPIs ──────────────────────────────────────────── -->
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

						<!-- Hours card -->
						<div class="rounded-xl border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/40 p-4 space-y-2">
							<div class="flex items-center gap-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
								<Clock class="w-3.5 h-3.5" />
								{{ translate("Reported Hours") }}
							</div>
							<div class="flex items-end gap-2">
								<span class="text-2xl font-bold text-gray-900 dark:text-gray-100">
									{{ formatHours(financials.total_hours) }}
								</span>
								<span v-if="financials.estimated_hours > 0" class="text-sm text-gray-500 pb-0.5">
									/ {{ formatHours(financials.estimated_hours) }} {{ translate("est.") }}
								</span>
							</div>

							<!-- Hours bar -->
							<div v-if="financials.estimated_hours > 0">
								<div class="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
									<div
										class="h-full rounded-full transition-all duration-500"
										:class="hoursOverBudget ? 'bg-red-500' : 'bg-indigo-500'"
										:style="{ width: hoursProgress + '%' }"
									></div>
								</div>
								<div class="flex justify-between text-xs mt-1">
									<span :class="hoursOverBudget ? 'text-red-600 font-semibold' : 'text-gray-500'">
										{{ hoursProgress }}%
										<span v-if="hoursOverBudget"> — {{ translate("Over budget!") }}</span>
									</span>
								</div>
							</div>

							<!-- Submitted vs draft -->
							<div class="flex gap-3 text-xs text-gray-500 pt-1">
								<span class="flex items-center gap-1">
									<CheckCircle2 class="w-3 h-3 text-green-500" />
									{{ translate("Submitted") }}: {{ formatHours(financials.submitted_hours) }}
								</span>
								<span v-if="financials.draft_hours > 0" class="flex items-center gap-1">
									<FileEdit class="w-3 h-3 text-amber-500" />
									{{ translate("Draft") }}: {{ formatHours(financials.draft_hours) }}
								</span>
							</div>
						</div>

						<!-- Budget Margin card (only when budget is set) -->
						<div
							v-if="financials.estimated_costing > 0"
							class="rounded-xl border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/40 p-4 space-y-2"
						>
							<div class="flex items-center gap-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
								<TrendingUp v-if="budgetMarginStatus !== 'bad'" class="w-3.5 h-3.5" />
								<TrendingDown v-else class="w-3.5 h-3.5 text-red-500" />
								{{ translate("Budget Margin") }}
							</div>
							<div class="flex items-end gap-2">
								<span
									class="text-2xl font-bold"
									:class="{
										'text-green-600': budgetMarginStatus === 'good',
										'text-amber-500': budgetMarginStatus === 'warn',
										'text-red-600': budgetMarginStatus === 'bad',
										'text-gray-900 dark:text-gray-100': !budgetMarginStatus,
									}"
								>
									{{ financials.per_budget_margin.toFixed(1) + '%' }}
								</span>
								<span class="text-sm text-gray-500 pb-0.5">
									{{ formatCurrency(financials.budget_margin) }}
								</span>
							</div>
							<!-- Budget utilization stacked progress bar -->
							<div class="mt-3">
								<div
									class="relative w-full h-2.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-visible flex"
									@mouseenter="showBudgetTooltip = true"
									@mouseleave="showBudgetTooltip = false"
								>

									<!-- Tooltip -->
									<div v-show="showBudgetTooltip" class="absolute bottom-full left-1/2 mb-2 z-50 pointer-events-none" style="transform: translateX(-50%)">
										<div class="bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg px-3 py-2 shadow-lg whitespace-nowrap">
											<div class="flex items-center gap-2 mb-1">
												<span class="w-2.5 h-2.5 rounded-sm bg-orange-600 inline-block flex-shrink-0"></span>
												<span class="text-gray-300">{{ translate("Total Internal Cost") }}:</span>
												<span class="font-semibold">{{ formatCurrency(financials.total_costing_amount) }} ({{ budgetSegments.timesheets.toFixed(1) }}%)</span>
											</div>
											<div v-if="financials.total_purchase_cost > 0" class="flex items-center gap-2 mb-1">
												<span class="w-2.5 h-2.5 rounded-sm bg-amber-400 inline-block flex-shrink-0"></span>
												<span class="text-gray-300">{{ translate("Purchase cost") }}:</span>
												<span class="font-semibold">{{ formatCurrency(financials.total_purchase_cost) }} ({{ budgetSegments.purchase.toFixed(1) }}%)</span>
											</div>
											<div v-if="financials.total_consumed_material_cost > 0" class="flex items-center gap-2 mb-1">
												<span class="w-2.5 h-2.5 rounded-sm bg-rose-400 inline-block flex-shrink-0"></span>
												<span class="text-gray-300">{{ translate("Material cost") }}:</span>
												<span class="font-semibold">{{ formatCurrency(financials.total_consumed_material_cost) }} ({{ budgetSegments.materials.toFixed(1) }}%)</span>
											</div>
											<div class="border-t border-gray-600 mt-1.5 pt-1.5 flex items-center gap-2">
												<span class="w-2.5 h-2.5 rounded-sm bg-gray-500 inline-block flex-shrink-0"></span>
												<span class="text-gray-300">{{ translate("Remaining") }}:</span>
												<span class="font-semibold">{{ formatCurrency(financials.budget_margin) }} ({{ (100 - budgetUtilization).toFixed(1) }}%)</span>
											</div>
											<!-- Arrow -->
											<div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
										</div>
									</div>
									<div
										class="h-full bg-indigo-500 transition-all duration-500"
										:style="{ width: budgetSegments.timesheets + '%' }"
									></div>
									<div
										class="h-full bg-amber-400 transition-all duration-500"
										:style="{ width: budgetSegments.purchase + '%' }"
									></div>
									<div
										class="h-full bg-rose-400 transition-all duration-500"
										:style="{ width: budgetSegments.materials + '%' }"
									></div>
								</div>
								<div class="flex justify-between text-xs mt-1.5">
									<div class="flex gap-3">
										<span class="flex items-center gap-1 text-indigo-500">
											<span class="w-2 h-2 rounded-full bg-indigo-500 inline-block"></span>
											{{ budgetSegments.timesheets.toFixed(1) }}%
										</span>
										<span v-if="budgetSegments.purchase > 0" class="flex items-center gap-1 text-amber-500">
											<span class="w-2 h-2 rounded-full bg-amber-400 inline-block"></span>
											{{ budgetSegments.purchase.toFixed(1) }}%
										</span>
										<span v-if="budgetSegments.materials > 0" class="flex items-center gap-1 text-rose-400">
											<span class="w-2 h-2 rounded-full bg-rose-400 inline-block"></span>
											{{ budgetSegments.materials.toFixed(1) }}%
										</span>
									</div>
									<span :class="budgetUtilization >= 100 ? 'text-red-600 font-semibold' : 'text-gray-500'">
										{{ budgetUtilization.toFixed(1) }}%
										<span v-if="budgetUtilization >= 100"> — {{ translate("Over budget!") }}</span>
									</span>
								</div>
							</div>

							<div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500 pt-1">
								<div>
									<span class="block text-gray-400">{{ translate("Budget") }}</span>
									<span class="font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(financials.estimated_costing) }}</span>
								</div>
								<div>
									<span class="block text-gray-400">{{ translate("Current cost") }}</span>
									<span class="font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(financials.total_current_cost) }}</span>
								</div>
								<div>
									<span class="block text-gray-400">{{ translate("Cost (timesheets)") }}</span>
									<span class="font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(financials.total_costing_amount) }}</span>
								</div>
								<div v-if="financials.total_purchase_cost > 0">
									<span class="block text-gray-400">{{ translate("Purchase cost") }}</span>
									<span class="font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(financials.total_purchase_cost) }}</span>
								</div>
								<div v-if="financials.total_consumed_material_cost > 0">
									<span class="block text-gray-400">{{ translate("Material cost") }}</span>
									<span class="font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(financials.total_consumed_material_cost) }}</span>
								</div>
							</div>
						</div>

						<!-- Team hours card -->
						<div
							v-if="financials.hours_per_user && financials.hours_per_user.length > 0"
							class="rounded-xl border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/40 p-4 space-y-2"
							:class="hasFinancialData ? '' : 'sm:col-span-2 lg:col-span-2'"
						>
							<div class="flex items-center gap-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
								<Users class="w-3.5 h-3.5" />
								{{ translate("Hours by Team Member") }}
							</div>
							<ul class="space-y-2 pt-1 max-h-48 overflow-y-auto pr-1">
								<li
									v-for="row in financials.hours_per_user"
									:key="row.user"
									class="flex items-center gap-2 text-sm"
								>
									<!-- Avatar initials -->
									<div class="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center flex-shrink-0">
										<span class="text-[10px] font-semibold text-indigo-600 dark:text-indigo-300">
											{{ (row.label || row.user).slice(0, 2).toUpperCase() }}
										</span>
									</div>
									<!-- Name + bar -->
									<div class="flex-1 min-w-0">
										<div class="flex items-center justify-between mb-0.5">
											<span class="text-xs text-gray-700 dark:text-gray-300 truncate max-w-[120px]" :title="row.label">
												{{ row.label }}
											</span>
											<span class="text-xs font-semibold text-gray-700 dark:text-gray-300 ml-2 flex-shrink-0">
												{{ formatHours(row.total) }}
											</span>
										</div>
										<div
											v-if="financials.total_hours > 0"
											class="w-full h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden"
										>
											<div
												class="h-full bg-indigo-400 dark:bg-indigo-500 rounded-full transition-all duration-500"
												:style="{ width: Math.round((row.total / financials.total_hours) * 100) + '%' }"
											></div>
										</div>
									</div>
								</li>
							</ul>
						</div>
					</div>
				</template>
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
	max-height: 700px;
	opacity: 1;
}
</style>
