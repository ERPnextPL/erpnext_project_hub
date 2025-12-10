<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import { X, Clock, Calendar, FileText, Plus } from 'lucide-vue-next'

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
	show: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['close', 'save'])

const store = useTaskStore()

// Form data
const formData = ref({
	hours: '',
	activity_type: '',
	description: '',
	from_time: '',
	to_time: '',
})

// Load activity types on mount
onMounted(() => {
	if (store.activityTypes.length === 0) {
		store.fetchActivityTypes()
	}
})

// Activity types from store
const activityTypes = computed(() => store.activityTypes)

// Reset form when modal opens
watch(() => props.show, (newVal) => {
	if (newVal) {
		resetForm()
		// Set default date to today
		const today = new Date().toISOString().split('T')[0]
		formData.value.from_time = `${today} 09:00:00`
		formData.value.to_time = `${today} 17:00:00`
		calculateHours()
	}
})

function resetForm() {
	formData.value = {
		hours: '',
		activity_type: '',
		description: '',
		from_time: '',
		to_time: '',
	}
}

function calculateHours() {
	if (formData.value.from_time && formData.value.to_time) {
		const from = new Date(formData.value.from_time)
		const to = new Date(formData.value.to_time)
		const diffMs = to - from
		const diffHours = diffMs / (1000 * 60 * 60)
		if (diffHours > 0) {
			formData.value.hours = diffHours.toFixed(2)
		}
	}
}

function handleSave() {
	// Validate hours
	if (!formData.value.hours || parseFloat(formData.value.hours) <= 0) {
		frappe.show_alert({ message: 'Please enter valid hours', indicator: 'red' })
		return
	}

	// Validate activity type
	if (!formData.value.activity_type || formData.value.activity_type.trim() === '') {
		frappe.show_alert({ message: 'Please select an activity type', indicator: 'red' })
		return
	}

	emit('save', {
		task: props.task.name,
		hours: parseFloat(formData.value.hours),
		activity_type: formData.value.activity_type,
		description: formData.value.description,
		from_time: formData.value.from_time,
		to_time: formData.value.to_time,
	})
}

function handleClose() {
	emit('close')
}
</script>

<template>
	<Teleport to="body">
		<Transition name="modal-fade">
			<div
				v-if="show"
				class="fixed inset-0 z-50 overflow-y-auto"
				@click.self="handleClose"
			>
				<!-- Overlay -->
				<div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>

				<!-- Modal -->
				<div class="flex min-h-full items-center justify-center p-4">
					<div
						class="relative bg-white rounded-lg shadow-xl max-w-md w-full transform transition-all"
						@click.stop
					>
						<!-- Header -->
						<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
							<div class="flex items-center gap-2">
								<Clock class="w-5 h-5 text-blue-600" />
								<h3 class="text-lg font-semibold text-gray-900">Log Time</h3>
							</div>
							<button
								@click="handleClose"
								class="p-1 rounded-md hover:bg-gray-100 text-gray-500"
							>
								<X class="w-5 h-5" />
							</button>
						</div>

						<!-- Body -->
						<div class="px-6 py-4 space-y-4">
							<!-- Task info -->
							<div class="bg-gray-50 rounded-md p-3">
								<p class="text-sm text-gray-500 mb-1">Task</p>
								<p class="text-sm font-medium text-gray-900">{{ task.subject }}</p>
								<p class="text-xs text-gray-500 mt-1">{{ task.name }}</p>
							</div>

							<!-- Hours -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									Hours <span class="text-red-500">*</span>
								</label>
								<input
									v-model="formData.hours"
									type="number"
									step="0.25"
									min="0"
									placeholder="e.g., 2.5"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								/>
							</div>

							<!-- Time range (optional) -->
							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-sm font-medium text-gray-700 mb-1">
										From
									</label>
									<input
										v-model="formData.from_time"
										type="datetime-local"
										@change="calculateHours"
										class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
									/>
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 mb-1">
										To
									</label>
									<input
										v-model="formData.to_time"
										type="datetime-local"
										@change="calculateHours"
										class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
									/>
								</div>
							</div>

							<!-- Activity Type -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									Activity Type <span class="text-red-500">*</span>
								</label>
								<select
									v-model="formData.activity_type"
									required
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								>
									<option value="" disabled>Select activity type...</option>
									<option v-for="type in activityTypes" :key="type" :value="type">
										{{ type }}
									</option>
								</select>
							</div>

							<!-- Description -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									Description
								</label>
								<textarea
									v-model="formData.description"
									rows="3"
									placeholder="What did you work on?"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								></textarea>
							</div>
						</div>

						<!-- Footer -->
						<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
							<button
								@click="handleClose"
								class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
							>
								Cancel
							</button>
							<button
								@click="handleSave"
								class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
							>
								Save Time Log
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
