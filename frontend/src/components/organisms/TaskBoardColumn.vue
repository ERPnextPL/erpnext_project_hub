<script setup>
import { ref, watch } from "vue";
import draggable from "vuedraggable";
import { ChevronsLeftRight, ChevronsRightLeft } from "lucide-vue-next";
import TaskCard from "../molecules/TaskCard.vue";
import BoardCardComposer from "../molecules/BoardCardComposer.vue";
import { translate } from "../../utils/translation";

/**
 * One list of the board: header, draggable cards and the "add a card" footer.
 * A collapsed column shrinks to a narrow bar that still accepts dropped cards.
 */
const props = defineProps({
	// { status, title, dot, accent, tasks }
	column: {
		type: Object,
		required: true,
	},
	collapsed: {
		type: Boolean,
		default: false,
	},
	// Function(task) -> extra props of the TaskCard (milestone, users...).
	cardProps: {
		type: Function,
		required: true,
	},
	activeMenuTask: {
		type: String,
		default: null,
	},
	dragging: {
		type: Boolean,
		default: false,
	},
	// Async function(subject) - when set, the column offers "Add a card".
	create: {
		type: Function,
		default: null,
	},
});

const emit = defineEmits([
	"toggle-collapse",
	"drop",
	"open",
	"menu",
	"update",
	"drag-start",
	"drag-end",
]);

// vuedraggable moves items between the arrays it is given, so every column
// works on its own copy that is refreshed whenever the tasks change.
const cards = ref([...props.column.tasks]);
watch(
	() => props.column.tasks,
	(tasks) => {
		cards.value = [...tasks];
	}
);

// A collapsed column only receives cards: its list stays empty and a dropped
// card is reported through "drop", then shows up once its status changes.
const NO_CARDS = Object.freeze([]);

function onChange(event) {
	if (event.added) emit("drop", event.added.element);
}

const dragOptions = {
	group: "task-board",
	sort: false,
	animation: 150,
	delay: 150,
	delayOnTouchOnly: true,
	ghostClass: "task-card-ghost",
	dragClass: "task-card-drag",
	chosenClass: "task-card-chosen",
};
</script>

<template>
	<!-- Collapsed: vertical bar -->
	<section
		v-if="collapsed"
		class="relative flex w-11 flex-shrink-0 flex-col items-center rounded-xl bg-gray-100 transition-colors"
		:class="dragging && 'ring-2 ring-inset ring-blue-300'"
	>
		<button
			type="button"
			class="flex flex-1 flex-col items-center gap-3 rounded-xl px-1 py-3 text-gray-700 hover:bg-gray-200/70"
			:title="translate('Expand list')"
			@click="emit('toggle-collapse')"
		>
			<ChevronsLeftRight class="h-4 w-4 text-gray-500" />
			<span :class="['h-2.5 w-2.5 rounded-full', column.dot]"></span>
			<span class="text-sm font-semibold [writing-mode:vertical-rl]">{{ column.title }}</span>
			<span class="rounded-full bg-white px-1.5 text-xs tabular-nums text-gray-600">
				{{ column.tasks.length }}
			</span>
		</button>
		<draggable
			:model-value="NO_CARDS"
			v-bind="dragOptions"
			item-key="name"
			class="absolute inset-0"
			:class="dragging ? 'z-10' : 'pointer-events-none'"
			@change="onChange"
		>
			<template #item="{ element }">
				<div :data-task="element.name" class="hidden"></div>
			</template>
		</draggable>
	</section>

	<!-- Expanded list -->
	<section
		v-else
		class="flex max-h-full w-72 flex-shrink-0 flex-col rounded-xl bg-gray-100 shadow-sm"
	>
		<header class="flex items-center gap-2 px-3 pb-1.5 pt-2.5">
			<span :class="['h-2.5 w-2.5 flex-shrink-0 rounded-full', column.dot]"></span>
			<h3 class="truncate text-sm font-semibold text-gray-800">
				{{ column.title }}
			</h3>
			<span class="rounded-full bg-white px-1.5 text-xs tabular-nums text-gray-600">
				{{ column.tasks.length }}
			</span>
			<span class="flex-1"></span>
			<button
				type="button"
				class="rounded-md p-1 text-gray-500 hover:bg-gray-200 hover:text-gray-800"
				:title="translate('Collapse list')"
				:aria-label="translate('Collapse list')"
				@click="emit('toggle-collapse')"
			>
				<ChevronsRightLeft class="h-4 w-4" />
			</button>
		</header>

		<draggable
			v-model="cards"
			v-bind="dragOptions"
			item-key="name"
			tag="div"
			class="board-column-cards flex min-h-[3rem] flex-1 flex-col gap-2 overflow-y-auto px-2 pb-2 pt-1"
			@change="onChange"
			@start="emit('drag-start')"
			@end="emit('drag-end')"
		>
			<template #item="{ element: task }">
				<TaskCard
					:task="task"
					v-bind="cardProps(task)"
					:menu-open="activeMenuTask === task.name"
					@open="emit('open', task)"
					@menu="(event) => emit('menu', task, event)"
					@update="(fields) => emit('update', task, fields)"
				/>
			</template>
			<template #footer>
				<div
					v-if="!cards.length"
					class="rounded-lg border-2 border-dashed border-gray-300 px-2 py-5 text-center text-xs text-gray-500"
				>
					{{ dragging ? translate("Drop here") : translate("No tasks") }}
				</div>
			</template>
		</draggable>

		<BoardCardComposer v-if="create" label="Add task" placeholder="Enter task name..." :create="create" />
	</section>
</template>

<style scoped>
.board-column-cards :deep(.task-card-ghost) {
	opacity: 0.35;
	background: var(--hub-drop-ghost-bg, rgb(219 234 254));
	border: 2px dashed var(--hub-drop-ghost-border, rgb(96 165 250));
}
.board-column-cards :deep(.task-card-ghost > *) {
	visibility: hidden;
}
:deep(.task-card-drag) {
	transform: rotate(3deg);
	box-shadow: 0 12px 24px rgb(0 0 0 / 0.18);
}
</style>
