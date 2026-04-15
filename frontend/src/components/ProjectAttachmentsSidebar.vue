<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useFileUpload } from "frappe-ui";
import {
	X,
	Paperclip,
	Upload,
	Trash2,
	Search,
	FileText,
	ChevronDown,
	ChevronUp,
} from "lucide-vue-next";
import { useTaskStore } from "../stores/taskStore";

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

const emit = defineEmits(["close"]);

const realWindow = typeof globalThis !== "undefined" ? globalThis.window : undefined;
const translate = (text) => {
	return typeof realWindow !== "undefined" && typeof realWindow.__ === "function"
		? realWindow.__(text)
		: text;
};

const store = useTaskStore();
const attachments = ref([]);
const attachmentsLoading = ref(false);
const attachmentsFetched = ref(false);
const isUploading = ref(false);
const uploadProgress = ref(0);
const fileInputRef = ref(null);
const isDragOver = ref(false);
const searchQuery = ref("");
const uploadSectionOpen = ref(true);
const listSectionOpen = ref(true);

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

function isImageFile(file) {
	return /^(jpg|jpeg|png|gif|webp|svg|bmp)$/i.test(file.file_type || "");
}

function formatFileSize(bytes) {
	if (!bytes) return "";
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function fetchAttachments() {
	if (!projectName.value) return;
	attachmentsLoading.value = true;
	try {
		attachments.value = await attachmentApiCall(
			"erpnext_projekt_hub.api.project_hub.get_project_attachments",
			{ project_name: projectName.value }
		);
	} catch (error) {
		console.error("Failed to load project attachments:", error);
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

function handleDragOver(event) {
	event.preventDefault();
	isDragOver.value = true;
}

function handleDragLeave() {
	isDragOver.value = false;
}

async function handleDrop(event) {
	event.preventDefault();
	isDragOver.value = false;
	const files = event.dataTransfer?.files;
	if (!files?.length) return;
	await uploadFiles(files);
}

async function uploadFiles(files) {
	if (!projectName.value) return;

	isUploading.value = true;
	uploadProgress.value = 0;
	const total = files.length;
	let completed = 0;
	const uploader = useFileUpload();

	try {
		for (const file of files) {
			const isImage = file?.type?.startsWith("image/");
			await uploader.upload(file, {
				doctype: "Project",
				docname: projectName.value,
				optimize: isImage,
				...(isImage ? { max_width: 1920, max_height: 1920 } : {}),
			});
			completed += 1;
			uploadProgress.value = Math.round((completed / total) * 100);
		}

		realWindow?.frappe?.show_alert({
			message: total === 1 ? translate("File added") : translate("Files added"),
			indicator: "green",
		});
		await fetchAttachments();
	} catch (error) {
		console.error("Project attachment upload failed:", error);
		realWindow?.frappe?.show_alert({
			message: error?.message || translate("Could not upload file"),
			indicator: "red",
		});
	} finally {
		isUploading.value = false;
		uploadProgress.value = 0;
	}
}

async function deleteAttachment(fileName) {
	if (!confirm(translate("Are you sure you want to delete this attachment?"))) return;

	try {
		await attachmentApiCall("erpnext_projekt_hub.api.project_hub.delete_project_attachment", {
			file_name: fileName,
		});
		attachments.value = attachments.value.filter((file) => file.name !== fileName);
		realWindow?.frappe?.show_alert({
			message: translate("Attachment deleted"),
			indicator: "green",
		});
	} catch (error) {
		console.error("Failed to delete project attachment:", error);
		realWindow?.frappe?.show_alert({
			message: error?.message || translate("Could not delete attachment"),
			indicator: "red",
		});
	}
}

function openAttachment(file) {
	realWindow?.open(file.file_url, "_blank");
}

watch(projectName, () => {
	attachmentsFetched.value = false;
	attachments.value = [];
	ensureAttachmentsLoaded();
});

onMounted(() => {
	ensureAttachmentsLoaded();
});

onUnmounted(() => {
});
</script>

<template>
	<aside
		class="project-attachments-sidebar h-full w-[420px] max-w-[92vw] bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden"
		@dragover="handleDragOver"
		@dragleave="handleDragLeave"
		@drop="handleDrop"
	>
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
			<button
				type="button"
				class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
				@click="emit('close')"
			>
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
					{{ translate("Choose from device") }}
				</button>
				<input
					ref="fileInputRef"
					type="file"
					accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv"
					multiple
					class="hidden"
					@change="handleFileSelect"
				/>
				<div class="flex-1 relative">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
					<input
						v-model="searchQuery"
						type="text"
						:placeholder="translate('Search attachments...')"
						class="w-full pl-10 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
					/>
				</div>
			</div>
		</div>

		<div class="flex-1 overflow-y-auto">
			<div
				class="px-4 py-4 transition-colors"
				:class="isDragOver ? 'bg-blue-50 dark:bg-blue-950/30' : ''"
			>
				<div
					class="rounded-lg border border-dashed p-4 text-center text-sm"
					:class="isDragOver ? 'border-blue-400 text-blue-700' : 'border-gray-200 text-gray-500'"
				>
					{{ translate("Drop files here to upload") }}
				</div>
			</div>

			<section class="px-4 pb-4">
				<button
					type="button"
					class="w-full flex items-center justify-between py-2 text-left"
					@click="uploadSectionOpen = !uploadSectionOpen"
				>
					<span class="text-sm font-medium text-gray-700 dark:text-gray-200">
						{{ translate("Upload") }}
					</span>
					<ChevronUp v-if="uploadSectionOpen" class="w-4 h-4 text-gray-400" />
					<ChevronDown v-else class="w-4 h-4 text-gray-400" />
				</button>
				<div v-show="uploadSectionOpen" class="space-y-2">
					<div v-if="isUploading" class="space-y-2">
						<div class="h-1.5 bg-gray-200 rounded-full overflow-hidden">
							<div
								class="h-full bg-blue-500 rounded-full transition-all"
								:style="{ width: uploadProgress + '%' }"
							/>
						</div>
						<p class="text-xs text-gray-500 text-center">
							{{ translate("Uploading") }}... {{ uploadProgress }}%
						</p>
					</div>
					<div v-else class="text-xs text-gray-500">
						{{ translate("Use the button above or drop files into the panel.") }}
					</div>
				</div>
			</section>

			<section class="px-4 pb-4">
				<button
					type="button"
					class="w-full flex items-center justify-between py-2 text-left"
					@click="listSectionOpen = !listSectionOpen"
				>
					<span class="text-sm font-medium text-gray-700 dark:text-gray-200">
						{{ translate("Files") }}
					</span>
					<ChevronUp v-if="listSectionOpen" class="w-4 h-4 text-gray-400" />
					<ChevronDown v-else class="w-4 h-4 text-gray-400" />
				</button>

				<div v-show="listSectionOpen">
					<div v-if="attachmentsLoading" class="py-8 text-center">
						<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto" />
					</div>
					<div v-else-if="filteredAttachments.length === 0" class="py-8 text-center text-sm text-gray-500">
						{{ translate("No attachments found") }}
					</div>
					<div v-else class="space-y-2">
						<div
							v-for="file in filteredAttachments"
							:key="file.name"
							class="group rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden hover:border-blue-300 transition-colors"
						>
							<button
								type="button"
								class="w-full flex items-center gap-3 p-3 text-left"
								@click="openAttachment(file)"
							>
								<div class="w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-700 flex items-center justify-center flex-shrink-0 overflow-hidden">
									<img
										v-if="isImageFile(file)"
										:src="file.file_url"
										:alt="file.file_name"
										class="w-full h-full object-cover"
										loading="lazy"
									/>
									<FileText v-else class="w-5 h-5 text-gray-400" />
								</div>
								<div class="min-w-0 flex-1">
									<div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
										{{ file.file_name }}
									</div>
									<div class="text-xs text-gray-500 truncate">
										{{ file.file_type || translate("File") }}
										<span v-if="file.file_size"> · {{ formatFileSize(file.file_size) }}</span>
									</div>
								</div>
							</button>
							<div class="flex items-center justify-between px-3 pb-3">
								<span class="text-[11px] text-gray-400">
									{{ file.is_private ? translate("Private") : translate("Public") }}
								</span>
								<button
									type="button"
									class="opacity-0 group-hover:opacity-100 p-1.5 rounded hover:bg-red-50 text-gray-500 hover:text-red-600 transition-opacity"
									@click.stop="deleteAttachment(file.name)"
								>
									<Trash2 class="w-4 h-4" />
								</button>
							</div>
						</div>
					</div>
				</div>
			</section>
		</div>
	</aside>
</template>
