<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import {
	Check,
	Clock,
	ExternalLink,
	Flag,
	Lock,
	PanelRightOpen,
	Trash2,
	Unlock,
	UserPlus,
} from "lucide-vue-next";
import { getStatusConfig, getStatusLabel } from "../../utils/taskStatus";
import { translate } from "../../utils/translation";

/**
 * Quick actions of a task (Trello's quick edit): status, priority, assignment,
 * blocked flag, time log. Emits actions only - the owner decides how to apply them.
 */
const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
	// { x, y } in viewport coordinates.
	anchor: {
		type: Object,
		required: true,
	},
	statuses: {
		type: Array,
		default: () => [],
	},
	priorities: {
		type: Array,
		default: () => [],
	},
	canAssignMe: {
		type: Boolean,
		default: true,
	},
	canLogTime: {
		type: Boolean,
		default: true,
	},
	canDelete: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits([
	"close",
	"open",
	"status",
	"priority",
	"assign-me",
	"toggle-blocked",
	"log-time",
	"open-desk",
	"delete",
]);

const PRIORITY_TONES = {
	Urgent: "text-red-600",
	High: "text-orange-600",
	Medium: "text-amber-600",
	Low: "text-slate-500",
};

const menuRef = ref(null);
const position = ref({ left: props.anchor.x, top: props.anchor.y });

function place() {
	const menu = menuRef.value;
	if (!menu) return;
	const margin = 8;
	const rect = menu.getBoundingClientRect();
	position.value = {
		left: Math.min(Math.max(margin, props.anchor.x), window.innerWidth - rect.width - margin),
		top: Math.min(Math.max(margin, props.anchor.y), window.innerHeight - rect.height - margin),
	};
}

function act(event, ...args) {
	emit(event, ...args);
	emit("close");
}

function onDocumentPointer(event) {
	if (menuRef.value && !menuRef.value.contains(event.target)) emit("close");
}

function onKeydown(event) {
	if (event.key === "Escape") emit("close");
}

watch(
	() => [props.anchor.x, props.anchor.y],
	() => {
		position.value = { left: props.anchor.x, top: props.anchor.y };
		nextTick(place);
	}
);

onMounted(() => {
	nextTick(place);
	setTimeout(() => document.addEventListener("mousedown", onDocumentPointer), 0);
	document.addEventListener("keydown", onKeydown);
	window.addEventListener("resize", place);
});

onUnmounted(() => {
	document.removeEventListener("mousedown", onDocumentPointer);
	document.removeEventListener("keydown", onKeydown);
	window.removeEventListener("resize", place);
});
</script>

<template>
	<Teleport to="body">
		<div
			ref="menuRef"
			role="menu"
			class="fixed z-50 max-h-[calc(100vh-16px)] w-60 overflow-y-auto rounded-xl border border-gray-200 bg-white py-1.5 text-sm shadow-xl"
			:style="{ left: position.left + 'px', top: position.top + 'px' }"
			@click.stop
		>
			<div class="truncate px-3 pb-1.5 text-xs font-semibold text-gray-500">
				{{ task.subject }}
			</div>

			<button type="button" role="menuitem" class="menu-item" @click="act('open', task)">
				<PanelRightOpen class="h-4 w-4" />
				{{ translate("Open task") }}
			</button>

			<template v-if="statuses.length">
				<div class="menu-section">{{ translate("Move to") }}</div>
				<button
					v-for="status in statuses"
					:key="status"
					type="button"
					role="menuitem"
					class="menu-item"
					:class="status === task.status && 'font-semibold'"
					@click="act('status', status)"
				>
					<span :class="['h-2.5 w-2.5 rounded-full', getStatusConfig(status).dot]"></span>
					<span class="flex-1">{{ getStatusLabel(status) }}</span>
					<Check v-if="status === task.status" class="h-4 w-4 text-blue-600" />
				</button>
			</template>

			<template v-if="priorities.length">
				<div class="menu-section">{{ translate("Priority") }}</div>
				<div class="flex flex-wrap gap-1 px-3 pb-1">
					<button
						v-for="priority in priorities"
						:key="priority"
						type="button"
						:class="[
							'inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs',
							PRIORITY_TONES[priority] || 'text-gray-600',
							priority === task.priority
								? 'border-current bg-gray-50 font-semibold'
								: 'border-gray-200 hover:bg-gray-50',
						]"
						@click="act('priority', priority)"
					>
						<Flag class="h-3 w-3" />
						{{ translate(priority) }}
					</button>
				</div>
			</template>

			<hr class="my-1.5 border-gray-100" />

			<button v-if="canAssignMe" type="button" role="menuitem" class="menu-item" @click="act('assign-me', task)">
				<UserPlus class="h-4 w-4" />
				{{ translate("Assign to me") }}
			</button>
			<button type="button" role="menuitem" class="menu-item" @click="act('toggle-blocked', task)">
				<component :is="task.is_blocked ? Unlock : Lock" class="h-4 w-4" />
				{{ task.is_blocked ? translate("Unblock") : translate("Mark as blocked") }}
			</button>
			<button v-if="canLogTime" type="button" role="menuitem" class="menu-item" @click="act('log-time', task)">
				<Clock class="h-4 w-4" />
				{{ translate("Add time") }}
			</button>
			<button type="button" role="menuitem" class="menu-item" @click="act('open-desk', task)">
				<ExternalLink class="h-4 w-4" />
				{{ translate("Open in Desk") }}
			</button>
			<template v-if="canDelete">
				<hr class="my-1.5 border-gray-100" />
				<button
					type="button"
					role="menuitem"
					class="menu-item text-red-600 hover:!bg-red-50"
					@click="act('delete', task)"
				>
					<Trash2 class="h-4 w-4" />
					{{ translate("Delete") }}
				</button>
			</template>
		</div>
	</Teleport>
</template>

<style scoped>
.menu-item {
	@apply flex w-full items-center gap-2 px-3 py-1.5 text-left text-gray-700 hover:bg-gray-100;
}
.menu-section {
	@apply px-3 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-wide text-gray-400;
}
</style>
