<script setup>
import { computed, onMounted, onUnmounted } from "vue";
import dayjs from "dayjs";
import { Check, ExternalLink, RefreshCw, X } from "lucide-vue-next";
import { translate } from "../../utils/translation";
import {
	deskUrl,
	formatNumber,
	getRequestStateClass,
	htmlToText,
} from "../../utils/customerRequests";
import { CHANGE_REQUEST_STATE_ALIASES } from "../../utils/changeRequests";
import { getStatusLabel as getTaskStatusLabel } from "../../utils/taskStatus";

const props = defineProps({
	request: {
		type: Object,
		required: true,
	},
	projectName: {
		type: String,
		required: true,
	},
	busy: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["close", "action", "open-customer-request"]);

const STAGES = ["Draft", "Task Created", "Done"];
const CANCELLED_STATE = "Cancelled";

const state = computed(() => props.request.workflow_state || "Draft");
const stageIndex = computed(() => STAGES.indexOf(CHANGE_REQUEST_STATE_ALIASES[state.value] || state.value));
const stateSince = computed(() =>
	props.request.state_changed_on ? dayjs(props.request.state_changed_on).format("DD.MM.YYYY HH:mm") : ""
);
const approvedAmount = computed(() =>
	props.request.approved_amount
		? `${formatNumber(props.request.approved_amount)} ${props.request.currency || ""}`.trim()
		: ""
);
const progress = computed(() => Math.max(0, Math.min(100, Number(props.request.task_progress) || 0)));
const taskUrl = computed(() =>
	props.request.task
		? `/project-hub/${encodeURIComponent(props.projectName)}/${encodeURIComponent(props.request.task)}`
		: ""
);

function stepClass(index) {
	if (state.value === CANCELLED_STATE) return "bg-gray-200";
	if (index < stageIndex.value) return "bg-green-500";
	if (index === stageIndex.value) return "bg-green-600";
	return "bg-gray-200";
}

function actionClass(action) {
	if (action.next_state === CANCELLED_STATE) {
		return "border border-red-300 bg-white text-red-800 hover:bg-red-50";
	}
	return "bg-gray-900 text-white hover:bg-gray-700";
}

function handleKeydown(event) {
	if (event.key === "Escape") emit("close");
}

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => window.removeEventListener("keydown", handleKeydown));
</script>

<template>
	<div class="fixed inset-0 z-40 flex justify-end bg-gray-900/30" @click.self="emit('close')">
		<aside
			:aria-label="translate('Change request details')"
			class="flex h-full w-[560px] max-w-full flex-col bg-white shadow-2xl"
		>
			<div class="flex flex-col gap-3 border-b border-gray-200 px-5 pb-4 pt-4 sm:px-6">
				<div class="flex items-center gap-2">
					<span class="font-mono text-xs text-gray-500">{{ request.name }}</span>
					<span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', getRequestStateClass(state)]">
						{{ translate(state) }}
					</span>
					<RefreshCw v-if="busy" class="h-3.5 w-3.5 animate-spin text-gray-400" />
					<span class="flex-1"></span>
					<a
						:href="deskUrl('Change Request', request.name)"
						target="_blank"
						rel="noopener noreferrer"
						class="inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-900"
					>
						{{ translate("Open in Desk") }}
						<ExternalLink class="h-3.5 w-3.5" />
					</a>
					<button
						type="button"
						class="rounded-md bg-gray-100 p-1.5 text-gray-600 hover:bg-gray-200"
						:aria-label="translate('Close')"
						@click="emit('close')"
					>
						<X class="h-4 w-4" />
					</button>
				</div>
				<h2 class="text-lg font-semibold leading-snug text-gray-900">{{ request.subject }}</h2>
				<ol class="grid grid-cols-3 gap-1" :aria-label="translate('Request stage')">
					<li v-for="(step, index) in STAGES" :key="step" class="flex flex-col gap-1">
						<span :class="['h-1 rounded-full', stepClass(index)]"></span>
						<span
							:class="[
								'text-[11px]',
								index === stageIndex ? 'font-semibold text-gray-900' : 'text-gray-500',
							]"
						>
							{{ translate(step) }}
						</span>
					</li>
				</ol>
				<div v-if="state === 'Cancelled'" class="text-xs font-medium text-red-700">
					{{ translate("Cancelled") }}
				</div>
			</div>

			<div class="flex flex-1 flex-col gap-5 overflow-y-auto px-5 py-4 text-sm sm:px-6">
				<dl class="grid grid-cols-2 gap-x-5 gap-y-3">
					<div>
						<dt class="text-xs text-gray-500">{{ translate("Customer Request") }}</dt>
						<dd class="mt-0.5">
							<button
								v-if="request.customer_request"
								type="button"
								class="font-mono text-xs text-blue-700 hover:underline"
								:title="translate('Show on the customer requests board')"
								@click="emit('open-customer-request', request.customer_request)"
							>
								{{ request.customer_request }}
							</button>
							<span v-else class="text-gray-900">-</span>
						</dd>
					</div>
					<div>
						<dt class="text-xs text-gray-500">{{ translate("In State Since") }}</dt>
						<dd class="mt-0.5 text-gray-900">{{ stateSince || "-" }}</dd>
					</div>
					<div>
						<dt class="text-xs text-gray-500">{{ translate("Approved Hours") }}</dt>
						<dd class="mt-0.5 text-gray-900">
							{{ request.approved_hours ? `${formatNumber(request.approved_hours)} h` : "-" }}
						</dd>
					</div>
					<div>
						<dt class="text-xs text-gray-500">{{ translate("Approved Amount") }}</dt>
						<dd class="mt-0.5 text-gray-900">{{ approvedAmount || "-" }}</dd>
					</div>
					<div v-if="request.quotation">
						<dt class="text-xs text-gray-500">{{ translate("Quotation") }}</dt>
						<dd class="mt-0.5">
							<a
								:href="deskUrl('Quotation', request.quotation)"
								target="_blank"
								rel="noopener noreferrer"
								class="text-blue-700 hover:underline"
							>
								{{ request.quotation }}
							</a>
						</dd>
					</div>
				</dl>

				<section
					v-if="state === 'Draft'"
					class="flex flex-col gap-1 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-900"
				>
					<h3 class="text-xs font-semibold uppercase tracking-wide">{{ translate("Before approval") }}</h3>
					<ul class="list-disc space-y-0.5 pl-5">
						<li>{{ translate("specification") }}</li>
						<li>{{ translate("sales order") }}</li>
						<li>{{ translate("order document signed by the customer") }}</li>
					</ul>
				</section>

				<section v-if="request.task" class="flex flex-col gap-2 rounded-xl border border-blue-100 bg-blue-50/60 p-4">
					<div class="flex items-center justify-between gap-2">
						<h3 class="text-xs font-semibold uppercase tracking-wide text-blue-900">{{ translate("Task") }}</h3>
						<a
							:href="taskUrl"
							target="_blank"
							class="inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-900"
						>
							{{ translate("Open in project") }}
							<ExternalLink class="h-3.5 w-3.5" />
						</a>
					</div>
					<div class="text-gray-900">{{ request.task_subject || request.task }}</div>
					<div class="flex items-center gap-3 text-xs text-blue-900">
						<span class="font-mono">{{ request.task }}</span>
						<span v-if="request.task_status">{{ getTaskStatusLabel(request.task_status) }}</span>
						<span>{{ progress }}%</span>
					</div>
					<div
						class="h-2 overflow-hidden rounded-full bg-blue-100"
						role="progressbar"
						:aria-valuenow="progress"
						aria-valuemin="0"
						aria-valuemax="100"
						:aria-label="translate('Task progress')"
					>
						<div class="h-full rounded-full bg-blue-600" :style="{ width: `${progress}%` }"></div>
					</div>
				</section>

				<section v-if="request.approved_scope" class="flex flex-col gap-1">
					<h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">
						{{ translate("Approved Scope") }}
					</h3>
					<p class="whitespace-pre-line leading-relaxed text-gray-800">{{ htmlToText(request.approved_scope) }}</p>
				</section>
			</div>

			<div
				v-if="request.actions?.length"
				class="flex flex-wrap items-center gap-2 border-t border-gray-200 px-5 py-3 sm:px-6"
			>
				<button
					v-for="action in request.actions"
					:key="action.action"
					type="button"
					:disabled="busy"
					:title="translate('Move to: {0}', [translate(CHANGE_REQUEST_STATE_ALIASES[action.next_state] || action.next_state)])"
					:class="[
						'inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50',
						actionClass(action),
					]"
					@click="emit('action', action)"
				>
					<X v-if="action.next_state === 'Cancelled'" class="h-4 w-4" />
					<Check v-else class="h-4 w-4" />
					{{ translate(action.action) }}
				</button>
			</div>
		</aside>
	</div>
</template>
