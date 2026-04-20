<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import { useTaskStore } from "../stores/taskStore";
import { X, Clock, Calendar, FileText, Plus } from "lucide-vue-next";
import { getRealWindow, translate } from "../utils/translation";

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
	show: {
		type: Boolean,
		default: false,
	},
	defaultHours: {
		type: Number,
		default: 1,
	},
	autoFocus: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["close", "save"]);

const store = useTaskStore();
const realWindow = getRealWindow();
const isSaving = ref(false);

const userLocale = computed(() => {
	const localeFromBoot = realWindow?.frappe?.boot?.lang;

	if (localeFromBoot) {
		return localeFromBoot;
	}

	if (typeof navigator !== "undefined" && navigator.language) {
		return navigator.language;
	}

	return "en-US";
});

const showAlert = (message) => {
	const frappe = realWindow?.frappe;
	if (frappe) {
		frappe.show_alert({ message: translate(message), indicator: "red" });
	}
};

// Form data
const formData = ref({
	hours: "",
	activity_type: "",
	description: "",
	from_time: "",
	to_time: "",
	is_billable: false,
});
const hoursInputRef = ref(null);

const DEFAULT_ACTIVITY_TYPE_KEY = "Execution";

const getPreferredActivityType = (availableTypes = []) => {
	if (!Array.isArray(availableTypes) || availableTypes.length === 0) {
		return "";
	}

	const globalDefaultActivityType = store.projectsSettings?.default_activity_type;
	if (globalDefaultActivityType && availableTypes.includes(globalDefaultActivityType)) {
		return globalDefaultActivityType;
	}

	const localizedFallback = translate(DEFAULT_ACTIVITY_TYPE_KEY);
	const fallbacks = [];
	if (localizedFallback) fallbacks.push(localizedFallback);
	if (!fallbacks.includes(DEFAULT_ACTIVITY_TYPE_KEY)) fallbacks.push(DEFAULT_ACTIVITY_TYPE_KEY);

	for (const candidate of fallbacks) {
		if (candidate && availableTypes.includes(candidate)) {
			return candidate;
		}
	}

	return availableTypes[0];
};

const applyDefaultActivityType = (availableTypes) => {
	const defaultType = getPreferredActivityType(availableTypes);
	if (defaultType) {
		formData.value.activity_type = defaultType;
	}
};

// Load activity types on mount
onMounted(() => {
	if (store.activityTypes.length === 0) {
		store.fetchActivityTypes();
	}
	// Add escape key listener
	document.addEventListener("keydown", handleEscapeKey);
});

// Remove escape key listener on unmount
onUnmounted(() => {
	document.removeEventListener("keydown", handleEscapeKey);
});

// Handle escape key
function handleEscapeKey(event) {
	if (event.key === "Escape" && props.show) {
		handleClose();
	}
}

// Activity types from store
const activityTypes = computed(() => store.activityTypes);

function resolveDefaultHours() {
	const candidate = typeof props.defaultHours === "number" ? props.defaultHours : parseFloat(props.defaultHours);
	return !Number.isNaN(candidate) && candidate > 0 ? candidate : 1;
}

// Reset form when modal opens
watch(
	() => props.show,
	(newVal) => {
		if (newVal) {
			isSaving.value = false;
			resetForm();
			// Set default date to today with current time minus 1 hour
			const now = new Date();
			const endTime = new Date(now.getTime() - 60 * 60 * 1000); // Subtract 1 hour
			const today = endTime.toISOString().split("T")[0];
			const hours = String(endTime.getHours()).padStart(2, "0");
			const minutes = String(endTime.getMinutes()).padStart(2, "0");
			formData.value.from_time = `${today}T${hours}:${minutes}`;
			formData.value.hours = String(resolveDefaultHours());
			// Set default activity type from global settings
			applyDefaultActivityType(activityTypes.value);
			calculateToTime();
			if (props.autoFocus) {
				nextTick(() => {
					if (hoursInputRef.value) {
						hoursInputRef.value.focus();
						hoursInputRef.value.select?.();
					}
				});
			}
		}
	},
	{ immediate: true }
);

watch(
	() => props.show,
	(newVal) => {
		if (!newVal) {
			isSaving.value = false;
		}
	}
);

// Watch for activity types to set default activity_type when they load
watch(activityTypes, (newTypes) => {
	if (props.show && newTypes.length > 0) {
		applyDefaultActivityType(newTypes);
	}
});

function resetForm() {
	formData.value = {
		hours: "",
		activity_type: "",
		description: "",
		from_time: "",
		to_time: "",
		is_billable: false,
	};
}

function calculateToTime() {
	if (formData.value.from_time && formData.value.hours) {
		const from = new Date(formData.value.from_time);
		const hours = parseFloat(formData.value.hours);

		if (!isNaN(hours) && hours > 0) {
			const to = new Date(from.getTime() + hours * 60 * 60 * 1000);
			// Keep local time string (YYYY-MM-DDTHH:mm) for preview
			const pad = (n) => String(n).padStart(2, "0");
			formData.value.to_time = `${to.getFullYear()}-${pad(to.getMonth() + 1)}-${pad(
				to.getDate()
			)}T${pad(to.getHours())}:${pad(to.getMinutes())}`;
		}
	}
}

function toFrappeDateTime(datetimeLocalStr) {
	if (!datetimeLocalStr) return "";
	// Convert 'YYYY-MM-DDTHH:mm' to 'YYYY-MM-DD HH:mm:ss'
	return `${datetimeLocalStr.replace("T", " ")}:00`;
}

function handleSave() {
	if (isSaving.value) {
		return;
	}

	// Validate hours
	if (!formData.value.hours || parseFloat(formData.value.hours) <= 0) {
		showAlert("Please enter a valid number of hours");
		return;
	}

	// Validate max 24 hours
	const hours = parseFloat(formData.value.hours);
	if (hours > 24) {
		showAlert("Cannot add more than 24 hours in one entry");
		return;
	}

	// Validate activity type
	if (!formData.value.activity_type || formData.value.activity_type.trim() === "") {
		showAlert("Please select an activity type");
		return;
	}

	// Validate description
	if (!formData.value.description || formData.value.description.trim() === "") {
		showAlert("Description is a required field");
		return;
	}

	if (formData.value.description.trim().length < 10) {
		showAlert("Description must have at least 10 characters");
		return;
	}

	// Calculate to_time before saving
	calculateToTime();

	isSaving.value = true;
	emit("save", {
		task: props.task.name,
		hours: parseFloat(formData.value.hours),
		activity_type: formData.value.activity_type,
		description: formData.value.description,
		from_time: toFrappeDateTime(formData.value.from_time),
		to_time: toFrappeDateTime(formData.value.to_time),
		is_billable: formData.value.is_billable ? 1 : 0,
	});
}

function formatDisplayTime(datetimeStr, localeOverride) {
	if (!datetimeStr) return "";
	const date = new Date(datetimeStr);
	const targetLocale = localeOverride || userLocale.value;
	return date.toLocaleString(targetLocale, {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
}

function handleClose() {
	emit("close");
}
</script>

<template>
	<Teleport to="body">
		<Transition name="modal-fade">
			<div v-if="show" class="fixed inset-0 z-50 overflow-y-auto" @click.self="handleClose">
				<!-- Overlay -->
				<div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>

				<!-- Modal -->
				<div class="flex min-h-full items-center justify-center p-4">
					<div
						class="relative bg-white rounded-lg shadow-xl max-w-md w-full transform transition-all"
						@click.stop
						role="dialog"
						aria-modal="true"
						aria-labelledby="timelog-modal-title"
					>
						<!-- Header -->
						<div
							class="flex items-center justify-between px-6 py-4 border-b border-gray-200"
						>
							<div class="flex items-center gap-2">
								<Clock class="w-5 h-5 text-blue-600" />
								<h3 id="timelog-modal-title" class="text-lg font-semibold text-gray-900">
									Dodaj czas
								</h3>
							</div>
							<button
								type="button"
								@click="handleClose"
								class="p-1 rounded-md hover:bg-gray-100 text-gray-500"
								:aria-label="translate('Close dialog')"
							>
								<X class="w-5 h-5" />
							</button>
						</div>

						<!-- Body -->
						<div class="px-6 py-4 space-y-4">
							<!-- Task info -->
							<div class="bg-gray-50 rounded-md p-3">
								<p class="text-sm text-gray-500 mb-1">Zadanie</p>
								<p class="text-sm font-medium text-gray-900">{{ task.subject }}</p>
								<p class="text-xs text-gray-500 mt-1">{{ task.name }}</p>
							</div>

							<!-- Hours -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									Godziny <span class="text-red-500">*</span>
								</label>
								<input
									v-model="formData.hours"
									ref="hoursInputRef"
									type="number"
									step="0.25"
									min="0"
									max="24"
									placeholder="e.g., 2.5"
									@input="calculateToTime"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								/>
								<p class="text-xs text-gray-500 mt-1">
									{{ translate("Maximum 24 hours per entry") }}
								</p>
							</div>

							<!-- Start time -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									{{ translate("Start Time") }}
								</label>
								<input
									v-model="formData.from_time"
									type="datetime-local"
									@change="calculateToTime"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
								/>
							</div>

							<!-- End time (calculated) -->
							<div v-if="formData.to_time" class="bg-gray-50 rounded-md p-3">
								<div class="flex items-center gap-2 text-sm text-gray-600">
									<Clock class="w-4 h-4" />
									<span
										>{{ translate("End Time") }}:
										{{ formatDisplayTime(formData.to_time) }}</span
									>
								</div>
							</div>

							<!-- Activity Type -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									{{ translate("Activity Type") }}
									<span class="text-red-500">*</span>
								</label>
								<select
									v-model="formData.activity_type"
									required
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								>
									<option value="" disabled>
										{{ translate("Select activity type...") }}
									</option>
									<option
										v-for="type in activityTypes"
										:key="type"
										:value="type"
									>
										{{ type }}
									</option>
								</select>
							</div>

							<!-- Is Billable -->
							<div class="flex items-center gap-3">
								<input
									id="timelog-is-billable"
									v-model="formData.is_billable"
									type="checkbox"
									class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
								/>
								<label for="timelog-is-billable" class="text-sm text-gray-700">
									{{ translate("Is Billable") }}
								</label>
							</div>

							<!-- Description -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									{{ translate("Description") }}
									<span class="text-red-500">*</span>
								</label>
								<textarea
									v-model="formData.description"
									required
									rows="3"
									:placeholder="
										translate('Work description (minimum 10 characters)...')
									"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								></textarea>
							</div>
						</div>

						<!-- Footer -->
						<div
							class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50"
						>
							<button
								@click="handleClose"
								class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
							>
								Anuluj
							</button>
							<button
								@click="handleSave"
								:disabled="isSaving"
								class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
							>
								{{ isSaving ? translate("Saving...") : translate("Save") }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
	transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
	opacity: 0;
}

.modal-fade-enter-active .bg-white,
.modal-fade-leave-active .bg-white {
	transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-fade-enter-from .bg-white,
.modal-fade-leave-to .bg-white {
	transform: scale(0.95);
	opacity: 0;
}
</style>
