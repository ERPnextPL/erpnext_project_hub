<script setup>
import { computed, ref } from "vue";
import { ChevronLeft, Lock, Plus } from "lucide-vue-next";
import RequestBoardCard from "./RequestBoardCard.vue";
import { translate } from "../../utils/translation";
import { formatAmounts, formatNumber, getRequestMoves } from "../../utils/customerRequests";

const props = defineProps({
	// Columns from buildBoardColumns().
	columns: {
		type: Array,
		required: true,
	},
	busyRequest: {
		type: String,
		default: "",
	},
	canAdd: {
		type: Boolean,
		default: false,
	},
	now: {
		type: Date,
		default: () => new Date(),
	},
});

const emit = defineEmits(["open", "move", "take", "convert", "add"]);

// Closed columns list only their latest requests until asked for all of them.
const CLOSED_COLUMN_LIMIT = 10;

const dragged = ref(null);
const dragOverState = ref("");
let dragActive = false;
const expandedColumns = ref(new Set());
const showAllColumns = ref(new Set());

const draggedMoves = computed(() => (dragged.value ? getRequestMoves(dragged.value) : {}));

const boardColumns = computed(() =>
	props.columns.map((column) => {
		const isSource = Boolean(dragged.value) && dragged.value.workflow_state === column.state;
		const move = draggedMoves.value[column.state] || null;
		const isTarget = Boolean(move);
		const isBlocked = Boolean(dragged.value) && !isSource && !isTarget;
		const collapsed = Boolean(column.closed) && !expandedColumns.value.has(column.state) && !isTarget;
		const limited =
			Boolean(column.closed) &&
			!showAllColumns.value.has(column.state) &&
			column.requests.length > CLOSED_COLUMN_LIMIT;

		return {
			...column,
			move,
			isTarget,
			isBlocked,
			isOver: isTarget && dragOverState.value === column.state,
			collapsed,
			visibleRequests: limited ? column.requests.slice(0, CLOSED_COLUMN_LIMIT) : column.requests,
			hiddenCount: limited ? column.requests.length - CLOSED_COLUMN_LIMIT : 0,
			summary: columnSummary(column),
		};
	})
);

function columnSummary(column) {
	const parts = [];
	if (column.hours) parts.push(`${formatNumber(column.hours)} h`);
	const amounts = formatAmounts(column.amounts);
	if (amounts) parts.push(amounts);
	if (parts.length) return parts.join(" · ");
	return column.requests.length ? translate("No estimate") : "";
}

function toggleSet(setRef, state) {
	const next = new Set(setRef.value);
	if (next.has(state)) next.delete(state);
	else next.add(state);
	setRef.value = next;
}

function onDragStart(event, request) {
	if (event.dataTransfer) {
		event.dataTransfer.effectAllowed = "move";
		event.dataTransfer.setData("text/plain", request.name);
	}
	// Re-rendering the dragged card inside dragstart cancels the drag in some
	// browsers, so mark it on the next tick.
	dragActive = true;
	setTimeout(() => {
		if (dragActive) dragged.value = request;
	}, 0);
}

function onDragEnd() {
	dragActive = false;
	dragged.value = null;
	dragOverState.value = "";
}

function onDragOver(event, column) {
	if (!column.isTarget) return;
	event.preventDefault();
	if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
	dragOverState.value = column.state;
}

function onDragLeave(event, column) {
	if (event.currentTarget?.contains(event.relatedTarget)) return;
	if (dragOverState.value === column.state) dragOverState.value = "";
}

function onDrop(event, column) {
	event.preventDefault();
	const request = dragged.value;
	onDragEnd();
	if (request && column.isTarget) emit("move", request, column.state);
}

function hasMoves(request) {
	return Object.keys(getRequestMoves(request)).length > 0;
}
</script>

<template>
	<div class="flex h-full min-h-0 items-stretch gap-3 overflow-x-auto px-4 pb-4 pt-3 sm:px-6">
		<section
			v-for="column in boardColumns"
			:key="column.state"
			:aria-label="translate(column.state)"
			:class="[
				'flex min-h-0 flex-shrink-0 flex-col rounded-xl border-2 transition-[opacity,background-color]',
				column.collapsed ? 'w-14' : 'w-72',
				column.isTarget ? ['border-dashed', column.target] : 'border-transparent bg-gray-100',
				column.isOver ? 'ring-4 ring-offset-0 ring-gray-200' : '',
				column.isBlocked ? 'opacity-50' : '',
			]"
			@dragover="onDragOver($event, column)"
			@dragleave="onDragLeave($event, column)"
			@drop="onDrop($event, column)"
		>
			<!-- Collapsed closed column: a narrow strip that expands on click -->
			<button
				v-if="column.collapsed"
				type="button"
				class="flex flex-1 flex-col items-center gap-3 py-3 text-gray-700 hover:bg-gray-200/60 rounded-xl"
				:title="translate('Expand column {0}', [translate(column.state)])"
				@click="toggleSet(expandedColumns, column.state)"
			>
				<span :class="['h-2.5 w-2.5 rounded-full', column.dot]"></span>
				<span class="rounded-full border border-gray-200 bg-white px-1.5 text-xs tabular-nums">
					{{ column.requests.length }}
				</span>
				<span class="text-sm font-semibold [writing-mode:vertical-rl]">{{ translate(column.state) }}</span>
			</button>

			<template v-else>
				<header class="flex flex-col gap-1 px-3 pb-2 pt-3">
					<div class="flex items-center gap-2">
						<span :class="['h-2.5 w-2.5 flex-shrink-0 rounded-full', column.dot]"></span>
						<h2 class="text-sm font-semibold text-gray-900">{{ translate(column.state) }}</h2>
						<span class="rounded-full border border-gray-200 bg-white px-1.5 text-xs tabular-nums text-gray-700">
							{{ column.requests.length }}
						</span>
						<span class="flex-1"></span>
						<button
							v-if="column.closed && !column.isTarget"
							type="button"
							class="rounded-md p-1 text-gray-500 hover:bg-gray-200"
							:title="translate('Collapse column')"
							@click="toggleSet(expandedColumns, column.state)"
						>
							<ChevronLeft class="h-4 w-4" />
						</button>
					</div>
					<div v-if="column.summary" class="text-xs text-gray-500">{{ column.summary }}</div>
					<div
						v-if="column.isTarget"
						:class="['mt-1 rounded-md border bg-white px-2 py-1 text-xs font-semibold', column.target, column.text]"
					>
						{{ translate("Drop to: {0}", [translate(column.move.action)]) }}
					</div>
					<div
						v-else-if="column.isBlocked"
						class="mt-1 flex items-center gap-1 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-600"
					>
						<Lock class="h-3 w-3" />
						{{ translate("Move not allowed") }}
					</div>
				</header>

				<div class="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-2.5 pb-3 pt-1">
					<RequestBoardCard
						v-for="request in column.visibleRequests"
						:key="request.name"
						:request="request"
						:movable="hasMoves(request)"
						:dragging="dragged?.name === request.name"
						:busy="busyRequest === request.name"
						:disabled="Boolean(busyRequest)"
						:now="now"
						@dragstart="onDragStart($event, request)"
						@dragend="onDragEnd"
						@open="emit('open', request)"
						@take="emit('take', request)"
						@convert="emit('convert', request)"
					/>

					<div
						v-if="column.requests.length === 0"
						class="rounded-lg border border-dashed border-gray-300 px-2 py-4 text-center text-xs text-gray-500"
					>
						{{ translate("No requests") }}
					</div>

					<button
						v-if="column.hiddenCount"
						type="button"
						class="py-1 text-xs text-gray-600 underline hover:text-gray-900"
						@click="toggleSet(showAllColumns, column.state)"
					>
						{{ translate("Show {0} older", [column.hiddenCount]) }}
					</button>

					<button
						v-if="column.state === 'Draft' && canAdd"
						type="button"
						class="flex items-center justify-center gap-1.5 rounded-lg border border-dashed border-gray-300 py-2 text-sm text-gray-600 hover:border-gray-400 hover:bg-white"
						@click="emit('add')"
					>
						<Plus class="h-4 w-4" />
						{{ translate("Add request") }}
					</button>
				</div>
			</template>
		</section>
	</div>
</template>
