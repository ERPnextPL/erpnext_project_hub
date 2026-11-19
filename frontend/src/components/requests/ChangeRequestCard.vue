<script setup>
import { computed } from "vue";
import { GripVertical, Hand, RefreshCw } from "lucide-vue-next";
import { translate } from "../../utils/translation";
import { daysInState, formatNumber } from "../../utils/customerRequests";
import { isStaleChangeRequest } from "../../utils/changeRequests";
import { getStatusLabel as getTaskStatusLabel } from "../../utils/taskStatus";

const props = defineProps({
	request: {
		type: Object,
		required: true,
	},
	// The card can be dragged: the user has somewhere to move it.
	movable: {
		type: Boolean,
		default: false,
	},
	dragging: {
		type: Boolean,
		default: false,
	},
	busy: {
		type: Boolean,
		default: false,
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	now: {
		type: Date,
		default: () => new Date(),
	},
});

const emit = defineEmits(["open", "take", "dragstart", "dragend"]);

const days = computed(() => daysInState(props.request, props.now));
const stale = computed(() => isStaleChangeRequest(props.request, props.now));
const ageLabel = computed(() => {
	if (days.value === null) return "";
	if (stale.value) return translate("{0} days waiting for approval", [days.value]);
	if (days.value === 0) return translate("today");
	return days.value === 1 ? translate("1 day") : translate("{0} days", [days.value]);
});

const approved = computed(() => {
	const parts = [];
	if (props.request.approved_hours) parts.push(`${formatNumber(props.request.approved_hours)} h`);
	if (props.request.approved_amount) {
		parts.push(`${formatNumber(props.request.approved_amount)} ${props.request.currency || ""}`.trim());
	}
	return parts.join(" · ");
});

const progress = computed(() => Math.max(0, Math.min(100, Number(props.request.task_progress) || 0)));
</script>

<template>
	<article
		:draggable="movable && !disabled"
		:class="[
			'group flex flex-col gap-2 rounded-lg border bg-white p-3 transition-shadow',
			dragging
				? 'border-dashed border-gray-400 opacity-40 shadow-none'
				: 'border-gray-200 shadow-sm hover:shadow-md',
			movable && !disabled ? 'cursor-grab active:cursor-grabbing' : '',
		]"
		@dragstart="emit('dragstart', $event)"
		@dragend="emit('dragend', $event)"
	>
		<div class="flex items-center gap-1.5 text-xs text-gray-500">
			<GripVertical v-if="movable" class="h-3.5 w-3.5 flex-shrink-0 text-gray-300 group-hover:text-gray-400" />
			<span class="truncate font-mono text-[11px]">{{ request.name }}</span>
			<span class="flex-1"></span>
			<RefreshCw v-if="busy" class="h-3.5 w-3.5 animate-spin text-gray-400" />
			<span v-if="request.customer_request" class="flex-shrink-0 font-mono text-[11px] text-gray-500">
				← {{ request.customer_request }}
			</span>
		</div>

		<button
			type="button"
			class="text-left text-sm font-medium leading-snug text-gray-900 hover:text-blue-700 focus:outline-none focus-visible:underline"
			@click="emit('open')"
		>
			{{ request.subject }}
		</button>

		<div v-if="approved || request.quotation" class="flex flex-wrap gap-1">
			<span v-if="approved" class="rounded bg-gray-100 px-1.5 py-0.5 text-xs tabular-nums text-gray-800">
				{{ approved }}
			</span>
			<span v-if="request.quotation" class="rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-900">
				{{ translate("Quotation") }} {{ request.quotation }}
			</span>
		</div>

		<div v-if="request.task" class="flex flex-col gap-1 rounded-md bg-blue-50/60 px-2 py-1.5">
			<div class="flex items-center justify-between gap-2 text-xs">
				<span class="truncate font-mono text-[11px] text-blue-900">{{ request.task }}</span>
				<span v-if="request.task_status" class="flex-shrink-0 text-blue-900">
					{{ getTaskStatusLabel(request.task_status) }}
				</span>
			</div>
			<div
				class="h-1.5 overflow-hidden rounded-full bg-blue-100"
				role="progressbar"
				:aria-valuenow="progress"
				aria-valuemin="0"
				aria-valuemax="100"
				:aria-label="translate('Task progress')"
			>
				<div class="h-full rounded-full bg-blue-600" :style="{ width: `${progress}%` }"></div>
			</div>
		</div>

		<div class="flex items-center justify-end">
			<button
				v-if="request.workflow_state === 'Draft' && !request.realization_assignee"
				type="button"
				:disabled="disabled"
				class="mr-auto inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
				@click="emit('take')"
			>
				<Hand class="h-3.5 w-3.5" />
				{{ translate("Take for realization") }}
			</button>
			<span v-else-if="request.realization_assignee" class="mr-auto text-xs text-gray-500">
				{{ translate("Assigned Implementer") }}:
				{{ request.realization_assignee_name || request.realization_assignee }}
			</span>
			<span
				v-if="ageLabel"
				:class="
					stale
						? 'rounded bg-orange-100 px-1.5 py-0.5 text-xs font-medium text-orange-800'
						: 'text-xs text-gray-500'
				"
				:title="translate('Time in the current stage')"
			>
				{{ ageLabel }}
			</span>
		</div>
	</article>
</template>
