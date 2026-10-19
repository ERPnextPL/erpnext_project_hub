<script setup>
import { ref } from "vue";
import { Paperclip, Plus, RefreshCw } from "lucide-vue-next";
import { translate } from "../../utils/translation";
import { decodeApiError, uploadRequestAttachment } from "../../utils/customerRequests";

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	name: {
		type: String,
		required: true,
	},
	attachments: {
		type: Array,
		default: () => [],
	},
});

const emit = defineEmits(["uploaded"]);

const fileInputRef = ref(null);
const uploading = ref(false);
const errorMessage = ref("");

async function handleFiles(event) {
	const files = Array.from(event.target.files || []);
	event.target.value = "";
	if (!files.length || uploading.value) return;

	uploading.value = true;
	errorMessage.value = "";
	try {
		for (const file of files) {
			await uploadRequestAttachment(props.doctype, props.name, file);
		}
		emit("uploaded");
	} catch (err) {
		console.error("Failed to attach file:", err);
		errorMessage.value = decodeApiError(err, translate("Failed to upload file"));
	} finally {
		uploading.value = false;
	}
}
</script>

<template>
	<div>
		<div class="flex items-center justify-between gap-2">
			<div class="text-xs font-medium uppercase tracking-wide text-gray-400">
				{{ translate("Attachments") }}
				<span v-if="attachments.length" class="font-normal">{{ attachments.length }}</span>
			</div>
			<button
				type="button"
				:disabled="uploading"
				class="inline-flex items-center gap-1 text-xs font-medium text-green-700 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300 disabled:opacity-50"
				@click="fileInputRef?.click()"
			>
				<RefreshCw v-if="uploading" class="h-3.5 w-3.5 animate-spin" />
				<Plus v-else class="h-3.5 w-3.5" />
				{{ uploading ? translate("Uploading...") : translate("Add Attachment") }}
			</button>
			<input ref="fileInputRef" type="file" multiple class="hidden" @change="handleFiles" />
		</div>
		<ul v-if="attachments.length" class="mt-1 space-y-0.5">
			<li v-for="file in attachments" :key="file.name" class="flex items-center gap-1 text-xs">
				<Paperclip class="h-3.5 w-3.5 flex-shrink-0 text-gray-400" />
				<a
					:href="file.file_url"
					target="_blank"
					rel="noopener noreferrer"
					class="truncate text-blue-700 hover:underline dark:text-blue-300"
					:title="file.file_name"
				>
					{{ file.file_name || file.file_url }}
				</a>
			</li>
		</ul>
		<p v-if="errorMessage" class="mt-1 text-xs text-red-600 dark:text-red-400">{{ errorMessage }}</p>
	</div>
</template>
