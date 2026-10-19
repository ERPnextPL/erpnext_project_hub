<script setup>
import { computed } from "vue";
import dayjs from "dayjs";
import { GitPullRequestArrow, GripVertical, Hand, RefreshCw } from "lucide-vue-next";
import { translate } from "../../utils/translation";
import {
	CONVERTED_STATE,
	daysInState,
	formatNumber,
	isStaleRequest,
} from "../../utils/customerRequests";

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

const emit = defineEmits(["open", "take", "convert", "dragstart", "dragend"]);

const AVATAR_COLORS = [
	"bg-blue-100 text-blue-800",
	"bg-pink-100 text-pink-800",
	"bg-green-100 text-green-800",
	"bg-amber-100 text-amber-800",
	"bg-violet-100 text-violet-800",
	"bg-cyan-100 text-cyan-800",
];

function initials(name) {
	const parts = String(name || "")
		.replace(/@.*/, "")
		.split(/[\s._-]+/)
		.filter(Boolean);
	return (parts[0]?.[0] || "?").toUpperCase() + (parts[1]?.[0] || "").toUpperCase();
}

function avatarColor(user) {
	let hash = 0;
	for (const char of String(user || "")) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
	return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

const assignees = computed(() => {
	const { analyst, analyst_name: name } = props.request;
	if (!analyst) return [];
	return [{ user: analyst, name: name || analyst, initials: initials(name || analyst), color: avatarColor(analyst) }];
});

const days = computed(() => daysInState(props.request, props.now));
const stale = computed(() => isStaleRequest(props.request, props.now));
const ageLabel = computed(() => {
	if (days.value === null) return "";
	if (stale.value) return translate("{0} days in this stage", [days.value]);
	if (days.value === 0) return translate("today");
	return days.value === 1 ? translate("1 day") : translate("{0} days", [days.value]);
});

const estimate = computed(() => {
	const parts = [];
	if (props.request.estimated_hours) parts.push(`${formatNumber(props.request.estimated_hours)} h`);
	if (props.request.estimated_amount) {
		parts.push(`${formatNumber(props.request.estimated_amount)} ${props.request.currency || ""}`.trim());
	}
	return parts.join(" · ");
});

const requestDate = computed(() =>
	props.request.request_date ? dayjs(props.request.request_date).format("DD.MM.YYYY") : ""
);

const isUnassignedAnalysis = computed(
	() => props.request.workflow_state === "To Analyze" && assignees.value.length === 0
);
const showConvert = computed(
	() => props.request.can_create_change_request && props.request.workflow_state !== CONVERTED_STATE
);
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
			<span v-if="request.source" class="flex-shrink-0 rounded bg-gray-100 px-1.5 py-0.5">
				{{ translate(request.source) }}
			</span>
		</div>

		<button
			type="button"
			class="text-left text-sm font-medium leading-snug text-gray-900 hover:text-blue-700 focus:outline-none focus-visible:underline"
			@click="emit('open')"
		>
			{{ request.subject }}
		</button>

		<div v-if="request.requested_by_name || requestDate" class="text-xs text-gray-500">
			{{ [request.requested_by_name, requestDate].filter(Boolean).join(" · ") }}
		</div>

		<div v-if="estimate || request.quotation || request.change_request" class="flex flex-wrap gap-1">
			<span v-if="estimate" class="rounded bg-gray-100 px-1.5 py-0.5 text-xs tabular-nums text-gray-800">
				{{ estimate }}
			</span>
			<span v-if="request.quotation" class="rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-900">
				{{ translate("Quotation") }} {{ request.quotation }}
			</span>
			<span v-if="request.change_request" class="rounded bg-violet-50 px-1.5 py-0.5 text-xs text-violet-800">
				{{ request.change_request }}
			</span>
		</div>

		<div class="flex min-h-[26px] items-center justify-between gap-2">
			<div class="flex items-center">
				<span
					v-for="(assignee, index) in assignees"
					:key="assignee.user"
					:title="assignee.name"
					:class="[
						'inline-flex h-6 w-6 items-center justify-center rounded-full border-2 border-white text-[10px] font-semibold',
						assignee.color,
						index ? '-ml-2' : '',
					]"
				>
					{{ assignee.initials }}
				</span>
				<button
					v-if="isUnassignedAnalysis"
					type="button"
					:disabled="disabled"
					class="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
					@click="emit('take')"
				>
					<Hand class="h-3.5 w-3.5" />
					{{ translate("Take for analysis") }}
				</button>
			</div>
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

		<button
			v-if="showConvert"
			type="button"
			:disabled="disabled"
			class="inline-flex items-center justify-center gap-1.5 rounded-md border border-violet-200 bg-violet-50 px-2 py-1.5 text-xs font-medium text-violet-800 hover:bg-violet-100 disabled:cursor-not-allowed disabled:opacity-50"
			@click="emit('convert')"
		>
			<GitPullRequestArrow class="h-3.5 w-3.5" />
			{{ translate("Create Change Request") }}
		</button>
	</article>
</template>
