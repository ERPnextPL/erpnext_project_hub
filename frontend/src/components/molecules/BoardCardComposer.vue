<script setup>
import { nextTick, ref } from "vue";
import { Plus, X } from "lucide-vue-next";
import { translate } from "../../utils/translation";

// "+ Add a card" footer of a board column. Stays open after adding, so several
// cards can be typed one after another, like in Trello.
const props = defineProps({
	label: {
		type: String,
		default: "Add a card",
	},
	placeholder: {
		type: String,
		default: "Enter a title for this card...",
	},
	// Async function(subject) creating the card.
	create: {
		type: Function,
		required: true,
	},
});

const open = ref(false);
const subject = ref("");
const saving = ref(false);
const textareaRef = ref(null);

async function start() {
	open.value = true;
	await nextTick();
	textareaRef.value?.focus();
}

function cancel() {
	// Keep the composer while a card is being saved: submit() clears the title afterwards.
	if (saving.value) return;
	open.value = false;
	subject.value = "";
}

async function submit() {
	const value = subject.value.trim();
	if (!value || saving.value) return;
	saving.value = true;
	try {
		await props.create(value);
		subject.value = "";
		await nextTick();
		textareaRef.value?.focus();
	} finally {
		saving.value = false;
	}
}

function onBlur() {
	if (!subject.value.trim() && !saving.value) cancel();
}
</script>

<template>
	<div class="px-2 pb-2">
		<form v-if="open" class="space-y-2" @submit.prevent="submit">
			<textarea
				ref="textareaRef"
				v-model="subject"
				rows="2"
				:placeholder="translate(placeholder)"
				:disabled="saving"
				class="block w-full resize-none rounded-lg border-0 bg-white p-2 text-sm text-gray-900 shadow-sm ring-1 ring-gray-200 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100 dark:ring-gray-700"
				@keydown.enter.exact.prevent="submit"
				@keydown.esc.prevent="cancel"
				@blur="onBlur"
			></textarea>
			<div class="flex items-center gap-1">
				<button
					type="submit"
					:disabled="saving || !subject.trim()"
					class="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
					@mousedown.prevent
				>
					{{ saving ? translate("Creating...") : translate(label) }}
				</button>
				<button
					type="button"
					class="rounded-md p-1.5 text-gray-500 hover:bg-gray-200 hover:text-gray-800 dark:hover:bg-gray-700 dark:hover:text-gray-100"
					:aria-label="translate('Cancel')"
					@mousedown.prevent
					@click="cancel"
				>
					<X class="h-4 w-4" />
				</button>
			</div>
		</form>
		<button
			v-else
			type="button"
			class="flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-gray-600 transition-colors hover:bg-gray-200/70 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-700/60 dark:hover:text-gray-100"
			@click="start"
		>
			<Plus class="h-4 w-4" />
			{{ translate(label) }}
		</button>
	</div>
</template>
