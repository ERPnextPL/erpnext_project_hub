<script setup>
import { computed, reactive, watch } from "vue";
import { X } from "lucide-vue-next";
import { translate } from "../utils/translation";
import DatePickerField from "./DatePickerField.vue";

const props = defineProps({
	open: Boolean,
	selectedCount: { type: Number, default: 0 },
	statuses: { type: Array, default: () => [] },
	priorities: { type: Array, default: () => [] },
	users: { type: Array, default: () => [] },
	loading: Boolean,
});
const emit = defineEmits(["close", "apply"]);
const form = reactive({
	priority: "",
	status: "",
	assignment_action: "",
	assignee: "",
	due_date_action: "",
	exp_end_date: "",
	expected_time_action: "",
	expected_time: "",
});

watch(() => props.open, (open) => {
	if (open) Object.assign(form, { priority: "", status: "", assignment_action: "", assignee: "", due_date_action: "", exp_end_date: "", expected_time_action: "", expected_time: "" });
});

const hasChanges = computed(() => Boolean(
	form.priority || form.status || form.assignment_action || form.due_date_action || form.expected_time_action
));

function submit() {
	if (!hasChanges.value || props.loading) return;
	const updates = {};
	if (form.priority) updates.priority = form.priority;
	if (form.status) updates.status = form.status;
	if (form.assignment_action) {
		updates.assignment_action = form.assignment_action;
		if (form.assignment_action === "set") updates.assignee = form.assignee;
	}
	if (form.due_date_action) updates.exp_end_date = form.due_date_action === "clear" ? null : form.exp_end_date;
	if (form.expected_time_action) updates.expected_time = form.expected_time_action === "clear" ? 0 : Number(form.expected_time);
	emit("apply", updates);
}
</script>

<template>
	<div v-if="open" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/30 p-4" @click.self="emit('close')">
		<div class="w-full max-w-lg rounded-xl bg-white shadow-xl">
			<div class="flex items-center justify-between border-b px-5 py-4">
				<div>
					<h2 class="text-lg font-semibold text-gray-900">{{ translate("Bulk edit tasks") }}</h2>
					<p class="text-sm text-gray-500">{{ selectedCount }} {{ translate("selected tasks") }}</p>
				</div>
				<button class="rounded p-1 text-gray-400 hover:bg-gray-100" @click="emit('close')"><X class="h-5 w-5" /></button>
			</div>
			<div class="grid gap-4 p-5 sm:grid-cols-2">
				<label class="text-sm text-gray-700">{{ translate("Priority") }}<select v-model="form.priority" class="mt-1 w-full rounded border-gray-300"><option value="">{{ translate("Keep unchanged") }}</option><option v-for="value in priorities" :key="value" :value="value">{{ translate(value) }}</option></select></label>
				<label class="text-sm text-gray-700">{{ translate("Status") }}<select v-model="form.status" class="mt-1 w-full rounded border-gray-300"><option value="">{{ translate("Keep unchanged") }}</option><option v-for="value in statuses" :key="value" :value="value">{{ translate(value) }}</option></select></label>
				<label class="text-sm text-gray-700">{{ translate("Assignment") }}<select v-model="form.assignment_action" class="mt-1 w-full rounded border-gray-300"><option value="">{{ translate("Keep unchanged") }}</option><option value="set">{{ translate("Assign to") }}</option><option value="clear">{{ translate("Clear assignment") }}</option></select></label>
				<label v-if="form.assignment_action === 'set'" class="text-sm text-gray-700">{{ translate("User") }}<select v-model="form.assignee" class="mt-1 w-full rounded border-gray-300"><option value="">{{ translate("Select user") }}</option><option v-for="user in users" :key="user.name" :value="user.name">{{ user.full_name || user.name }}</option></select></label>
				<label class="text-sm text-gray-700">{{ translate("Due date") }}<select v-model="form.due_date_action" class="mt-1 w-full rounded border-gray-300"><option value="">{{ translate("Keep unchanged") }}</option><option value="set">{{ translate("Set date") }}</option><option value="clear">{{ translate("Clear date") }}</option></select></label>
				<label v-if="form.due_date_action === 'set'" class="text-sm text-gray-700">{{ translate("Date") }}<DatePickerField id="bulk-task-due-date" v-model="form.exp_end_date" /></label>
				<label class="text-sm text-gray-700">{{ translate("Expected time") }}<select v-model="form.expected_time_action" class="mt-1 w-full rounded border-gray-300"><option value="">{{ translate("Keep unchanged") }}</option><option value="set">{{ translate("Set value") }}</option><option value="clear">{{ translate("Clear value") }}</option></select></label>
				<label v-if="form.expected_time_action === 'set'" class="text-sm text-gray-700">{{ translate("Hours") }}<input v-model="form.expected_time" type="number" min="0" step="0.25" class="mt-1 w-full rounded border-gray-300" /></label>
			</div>
			<div class="flex justify-end gap-2 border-t px-5 py-4"><button class="rounded border px-4 py-2 text-sm" @click="emit('close')">{{ translate("Cancel") }}</button><button class="rounded bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50" :disabled="!hasChanges || (form.assignment_action === 'set' && !form.assignee) || (form.due_date_action === 'set' && !form.exp_end_date) || (form.expected_time_action === 'set' && form.expected_time === '') || loading" @click="submit">{{ loading ? translate("Saving...") : translate("Apply changes") }}</button></div>
		</div>
	</div>
</template>
