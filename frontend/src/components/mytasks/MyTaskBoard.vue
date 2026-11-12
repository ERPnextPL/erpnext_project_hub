<script setup>
import { computed, ref } from "vue";
import { Calendar, Flag, Folder, ListChecks, CornerDownRight, User } from "lucide-vue-next";
import { useMyTasksStore } from "../../stores/myTasksStore";
import { BOARD_STATUSES, getStatusConfig, getStatusLabel } from "../../utils/taskStatus";
import BlockedToggle from "../shared/BlockedToggle.vue";

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text, args) => {
	const out =
		typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
			? realWindow.__(text, args)
			: text;
	return out;
};

const store = useMyTasksStore();

// ERPNext task statuses are fixed, so columns are fixed too. Closed statuses are
// shown only when they hold tasks or were explicitly selected in the filter.
const CLOSED = ["Completed", "Cancelled"];
const columns = computed(() => {
	const filtered = store.filters?.status || [];
	return BOARD_STATUSES.map((status) => ({
		status,
		label: getStatusLabel(status),
		config: getStatusConfig(status),
		tasks: (store.tasks || []).filter((t) => (t.status || "Open") === status),
	})).filter(
		(col) => !CLOSED.includes(col.status) || col.tasks.length > 0 || filtered.includes(col.status)
	);
});

// Project label colours: stable per project name
const LABEL_PALETTE = [
	"bg-violet-100 text-violet-800",
	"bg-emerald-100 text-emerald-800",
	"bg-pink-100 text-pink-800",
	"bg-sky-100 text-sky-800",
	"bg-orange-100 text-orange-800",
	"bg-teal-100 text-teal-800",
	"bg-indigo-100 text-indigo-800",
	"bg-lime-100 text-lime-800",
];
function projectLabelClass(task) {
	const key = task.project || task.project_name || "";
	let hash = 0;
	for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) >>> 0;
	return LABEL_PALETTE[hash % LABEL_PALETTE.length];
}

const PRIORITY_CLASSES = {
	Urgent: "bg-red-100 text-red-700",
	High: "bg-orange-100 text-orange-700",
	Medium: "bg-yellow-100 text-yellow-700",
	Low: "bg-gray-100 text-gray-600",
};

function dueInfo(task) {
	if (!task.exp_end_date) return null;
	const due = new Date(String(task.exp_end_date).slice(0, 10) + "T00:00:00");
	const today = new Date();
	today.setHours(0, 0, 0, 0);
	const diff = Math.round((due - today) / 86400000);
	const closed = CLOSED.includes(task.status);
	const text = due.toLocaleDateString("pl-PL", { day: "2-digit", month: "2-digit" });
	if (!closed && (task.is_overdue || diff < 0))
		return { text, label: translate("Overdue"), cls: "bg-red-50 text-red-700" };
	if (!closed && diff === 0) return { text, label: translate("Today"), cls: "bg-amber-50 text-amber-700" };
	if (!closed && diff === 1) return { text, label: translate("Tomorrow"), cls: "bg-blue-50 text-blue-700" };
	return { text, label: "", cls: "bg-gray-100 text-gray-600" };
}

function assignee(task) {
	if (!task._assign) return null;
	try {
		const list = JSON.parse(task._assign);
		if (Array.isArray(list) && list.length) {
			const email = list[0];
			return { email, initials: email.charAt(0).toUpperCase(), extra: list.length - 1 };
		}
	} catch {
		return null;
	}
	return null;
}

// Drag and drop between columns changes the status
const draggedName = ref(null);
const overStatus = ref(null);

function onDragStart(event, task) {
	draggedName.value = task.name;
	event.dataTransfer.effectAllowed = "move";
	event.dataTransfer.setData("text/plain", task.name);
}
function onDragEnd() {
	draggedName.value = null;
	overStatus.value = null;
}
function onDragOver(event, status) {
	if (!draggedName.value) return;
	event.preventDefault();
	event.dataTransfer.dropEffect = "move";
	overStatus.value = status;
}
async function onDrop(event, status) {
	event.preventDefault();
	const name = draggedName.value;
	onDragEnd();
	const task = store.tasks.find((t) => t.name === name);
	if (!task || (task.status || "Open") === status) return;
	try {
		await store.quickUpdateTask(name, { status });
		realWindow?.frappe?.show_alert?.({
			message: translate("Task moved to {0}", [getStatusLabel(status)]),
			indicator: "green",
		});
	} catch {
		realWindow?.frappe?.show_alert?.({
			message: translate("Failed to update task"),
			indicator: "red",
		});
	}
}

function setBlocked(task, blocked) {
	store.quickUpdateTask(task.name, { is_blocked: blocked ? 1 : 0 });
}
</script>

<template>
	<div class="-mx-4 sm:-mx-6 lg:-mx-8 overflow-x-auto pb-4">
		<div class="flex items-start gap-3 px-4 sm:px-6 lg:px-8 min-w-max">
			<section
				v-for="column in columns"
				:key="column.status"
				:aria-label="column.label"
				class="w-72 flex-shrink-0 rounded-2xl bg-gray-200/70 flex flex-col max-h-[calc(100vh-14rem)] transition-colors"
				:class="overStatus === column.status ? 'bg-blue-100 ring-2 ring-blue-300 ring-inset' : ''"
				@dragover="onDragOver($event, column.status)"
				@dragleave="overStatus = null"
				@drop="onDrop($event, column.status)"
			>
				<header class="flex items-center gap-2 px-3 pt-3 pb-2">
					<span class="w-2.5 h-2.5 rounded-full" :class="column.config.dot"></span>
					<h3 class="text-sm font-semibold text-gray-800 flex-1">{{ column.label }}</h3>
					<span class="text-xs text-gray-600 bg-white/70 rounded-full px-2 py-0.5">
						{{ column.tasks.length }}
					</span>
				</header>

				<div class="flex-1 overflow-y-auto px-2 pb-2 space-y-2 min-h-[4rem]">
					<article
						v-for="task in column.tasks"
						:key="task.name"
						draggable="true"
						tabindex="0"
						class="group rounded-xl bg-white p-3 shadow-sm hover:shadow-md hover:bg-gray-50 cursor-pointer transition-shadow space-y-2"
						:class="draggedName === task.name ? 'opacity-40' : ''"
						@dragstart="onDragStart($event, task)"
						@dragend="onDragEnd"
						@click="store.selectTask(task)"
						@keydown.enter="store.selectTask(task)"
					>
						<!-- Labels: project (colour by project), blocked, priority -->
						<div class="flex flex-wrap items-center gap-1">
							<span
								v-if="task.project_name"
								class="inline-flex max-w-full items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium"
								:class="projectLabelClass(task)"
								:title="task.project_name"
							>
								<Folder class="w-3 h-3 flex-shrink-0" />
								<span class="truncate">{{ task.project_name }}</span>
							</span>
							<span
								v-if="task.priority && task.priority !== 'Medium' && task.priority !== 'Low'"
								class="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium"
								:class="PRIORITY_CLASSES[task.priority]"
							>
								<Flag class="w-3 h-3" />
								{{ task.priority }}
							</span>
						</div>

						<!-- Parent reference for subtasks (they are separate cards) -->
						<div
							v-if="task.parent_task"
							class="flex items-center gap-1 text-[11px] text-gray-500"
							:title="task.parent_subject || task.parent_task"
						>
							<CornerDownRight class="w-3 h-3 flex-shrink-0" />
							<span class="truncate">{{ task.parent_subject || task.parent_task }}</span>
						</div>

						<div class="flex items-start gap-2">
							<p class="flex-1 text-sm font-medium text-gray-900 leading-snug break-words">
								{{ task.subject }}
							</p>
							<span @click.stop>
								<BlockedToggle
									:blocked="task.is_blocked"
									@toggle="(blocked) => setBlocked(task, blocked)"
								/>
							</span>
						</div>

						<div
							v-if="task.progress > 0 && task.progress < 100"
							class="h-1 rounded bg-gray-200 overflow-hidden"
							:title="`${task.progress}%`"
						>
							<div class="h-full bg-emerald-500" :style="{ width: task.progress + '%' }"></div>
						</div>

						<div class="flex items-center gap-2 text-xs text-gray-500">
							<span
								v-if="dueInfo(task)"
								class="inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-medium"
								:class="dueInfo(task).cls"
							>
								<Calendar class="w-3 h-3" />
								{{ dueInfo(task).label ? dueInfo(task).label + " · " : "" }}{{ dueInfo(task).text }}
							</span>
							<span
								v-if="task.subtask_count > 0"
								class="inline-flex items-center gap-1"
								:class="task.subtask_done === task.subtask_count ? 'text-emerald-600' : ''"
								:title="translate('Subtasks')"
							>
								<ListChecks class="w-3.5 h-3.5" />
								{{ task.subtask_done || 0 }}/{{ task.subtask_count }}
							</span>
							<span class="flex-1"></span>
							<span
								v-if="assignee(task)"
								class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-[11px] font-semibold text-blue-700"
								:title="assignee(task).email"
							>
								{{ assignee(task).initials }}
							</span>
							<span
								v-else
								class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-gray-100"
							>
								<User class="w-3 h-3 text-gray-400" />
							</span>
						</div>
					</article>

					<div
						v-if="column.tasks.length === 0"
						class="rounded-xl border border-dashed border-gray-300 py-6 text-center text-xs text-gray-400"
					>
						{{ translate("No tasks") }}
					</div>
				</div>
			</section>
		</div>
	</div>
</template>
