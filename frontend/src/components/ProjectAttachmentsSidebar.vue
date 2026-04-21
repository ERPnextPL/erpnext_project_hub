<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { X, Paperclip, Upload, Trash2, Search, FileText } from "lucide-vue-next";

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
	project: {
		type: Object,
		default: null,
	},
});

const emit = defineEmits(["close", "updated"]);

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text) =>
	typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
		? realWindow.__(text)
		: text;

const attachments = ref([]);
const attachmentsLoading = ref(false);
const attachmentsFetched = ref(false);
const errorMessage = ref("");
const isUploading = ref(false);
const uploadProgress = ref(0);
const fileInputRef = ref(null);
const searchQuery = ref("");

function getCsrfToken() {
	if (realWindow?.frappe?.csrf_token && realWindow.frappe.csrf_token !== "None") {
		return realWindow.frappe.csrf_token;
	}
	if (realWindow?.csrf_token && realWindow.csrf_token !== "{{ csrf_token }}") {
		return realWindow.csrf_token;
	}
	return "";
}

async function attachmentApiCall(method, params = {}) {
	const formData = new FormData();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined) {
			formData.append(key, value);
		}
	});

	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		headers: { "X-Frappe-CSRF-Token": getCsrfToken() },
		body: formData,
	});
	const data = await response.json();
	if (data.exc) throw new Error(data._server_messages || "API error");
	return data.message;
}

const projectName = computed(() => props.project?.name || props.projectId);

const filteredAttachments = computed(() => {
	const query = searchQuery.value.trim().toLowerCase();
	if (!query) return attachments.value;
	return attachments.value.filter((file) =>
		[file.file_name, file.file_type].some((value) =>
			String(value || "").toLowerCase().includes(query)
		)
	);
});

function formatFileSize(bytes) {
	if (!bytes) return "";
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function fetchAttachments() {
	if (!projectName.value) return;
	attachmentsLoading.value = true;
	errorMessage.value = "";
	try {
		attachments.value = await attachmentApiCall(
			"erpnext_projekt_hub.api.project_hub.get_project_attachments",
			{ project_name: projectName.value }
		);
		emit("updated", attachments.value.length);
	} catch (error) {
		errorMessage.value = error?.message || translate("Failed to load attachments");
	} finally {
		attachmentsLoading.value = false;
	}
}

function ensureAttachmentsLoaded() {
	if (!attachmentsFetched.value) {
		attachmentsFetched.value = true;
		fetchAttachments();
	}
}

function triggerFileInput() {
	fileInputRef.value?.click();
}

async function handleFileSelect(event) {
	const files = event.target.files;
	if (!files?.length) return;
	await uploadFiles(files);
	event.target.value = "";
}

async function uploadFiles(files) {
	if (!projectName.value) return;

	isUploading.value = true;
	uploadProgress.value = 0;
	errorMessage.value = "";
	const total = files.length;
	let completed = 0;

	try {
		for (const file of files) {
			await uploadSingleFile(file);
			completed += 1;
			uploadProgress.value = Math.round((completed / total) * 100);
		}
		await fetchAttachments();
	} catch (error) {
		errorMessage.value = error?.message || translate("Failed to upload file");
	} finally {
		isUploading.value = false;
		uploadProgress.value = 0;
	}
}

function uploadSingleFile(file) {
	return new Promise((resolve, reject) => {
		const formData = new FormData();
		formData.append("file", file);
		formData.append("doctype", "Project");
		formData.append("docname", projectName.value);
		formData.append("folder", "Home");
		formData.append("is_private", 1);

		const xhr = new XMLHttpRequest();
		xhr.open("POST", "/api/method/upload_file", true);
		xhr.setRequestHeader("Accept", "application/json");

		const csrfToken = getCsrfToken();
		if (csrfToken) {
			xhr.setRequestHeader("X-Frappe-CSRF-Token", csrfToken);
		}

		xhr.onload = () => {
			let response;
			try {
				response = JSON.parse(xhr.responseText);
			} catch (error) {
				reject(new Error(translate("Failed to upload file")));
				return;
			}

			if (xhr.status >= 200 && xhr.status < 300) {
				resolve(response);
				return;
			}

			const serverMessages = response?._server_messages
				? JSON.parse(response._server_messages)
						.map((message) => {
							try {
								return JSON.parse(message).message;
							} catch (error) {
								return message;
							}
						})
						.filter(Boolean)
				: [];

			const message =
				serverMessages.join("\n") ||
				response?._error_message ||
				response?.message ||
				translate("Failed to upload file");

			reject(new Error(message));
		};

		xhr.onerror = () => reject(new Error(translate("Failed to upload file")));
		xhr.send(formData);
	});
}

async function deleteAttachment(fileName) {
	if (!confirm(translate("Are you sure you want to delete this attachment?"))) return;
	errorMessage.value = "";
	try {
		await attachmentApiCall("erpnext_projekt_hub.api.project_hub.delete_project_attachment", {
			file_name: fileName,
		});
		attachments.value = attachments.value.filter((file) => file.name !== fileName);
		emit("updated", attachments.value.length);
	} catch (error) {
		errorMessage.value = error?.message || translate("Failed to delete attachment");
	}
}

watch(projectName, () => {
	attachmentsFetched.value = false;
	attachments.value = [];
	ensureAttachmentsLoaded();
});

onMounted(() => {
	ensureAttachmentsLoaded();
});
</script>

<template>
	<aside class="h-full w-[420px] max-w-[92vw] bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
		<header class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
			<div class="flex items-center gap-2 min-w-0">
				<Paperclip class="w-4 h-4 text-gray-400 flex-shrink-0" />
				<div class="min-w-0">
					<div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
						{{ translate("Attachments") }}
					</div>
					<div class="text-xs text-gray-500">
						{{ filteredAttachments.length }} {{ translate("files") }}
					</div>
				</div>
			</div>
			<button type="button" class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500" @click="emit('close')">
				<X class="w-4 h-4" />
			</button>
		</header>

		<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40">
			<div class="flex items-center gap-2">
				<button
					type="button"
					class="inline-flex items-center gap-1.5 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:border-blue-300 hover:text-blue-700 dark:hover:text-blue-300"
					@click="triggerFileInput"
				>
					<Upload class="w-4 h-4" />
					{{ translate("Add files") }}
				</button>
				<div class="relative flex-1 min-w-0">
					<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
					<input
						v-model="searchQuery"
						type="text"
						:placeholder="translate('Search files...')"
						class="w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 pl-9 pr-3 py-2 text-sm text-gray-900 dark:text-gray-100"
					/>
				</div>
				<input ref="fileInputRef" type="file" class="hidden" multiple @change="handleFileSelect" />
			</div>
		</div>

		<div class="flex-1 overflow-y-auto p-4">
			<div v-if="errorMessage" class="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-200">
				{{ errorMessage }}
			</div>
			<div v-if="isUploading" class="mb-4 text-sm text-gray-600 dark:text-gray-300">
				{{ translate("Uploading") }}... {{ uploadProgress }}%
			</div>
			<div v-else-if="attachmentsLoading" class="py-6 text-center text-sm text-gray-500">
				{{ translate("Loading") }}...
			</div>
			<div v-else-if="filteredAttachments.length === 0" class="rounded-xl border border-dashed border-gray-300 px-4 py-6 text-center text-sm text-gray-500">
				{{ translate("No attachments yet") }}
			</div>
			<div v-else class="space-y-3">
				<div
					v-for="file in filteredAttachments"
					:key="file.name"
					class="group rounded-xl border border-gray-200 dark:border-gray-700 p-3 hover:border-blue-300 dark:hover:border-blue-700 cursor-pointer"
					@click="realWindow?.open(file.file_url, '_blank', 'noopener,noreferrer')"
				>
					<div class="flex items-start gap-3">
						<div class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
							<FileText class="h-5 w-5 text-gray-400" />
						</div>
						<div class="min-w-0 flex-1">
							<div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
								{{ file.file_name }}
							</div>
							<div class="text-xs text-gray-500">
								{{ formatFileSize(file.file_size) }}
							</div>
						</div>
						<button
							type="button"
							class="opacity-0 group-hover:opacity-100 p-1.5 rounded-md hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600"
							@click.stop="deleteAttachment(file.name)"
						>
							<Trash2 class="h-4 w-4" />
						</button>
					</div>
				</div>
			</div>
		</div>
	</aside>
</template>
