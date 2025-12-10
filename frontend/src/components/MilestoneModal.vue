<script setup>
import { ref, watch } from 'vue'
import { Diamond, X } from 'lucide-vue-next'

const props = defineProps({
	show: Boolean,
	milestone: Object,
	editMode: Boolean
})

const emit = defineEmits(['save', 'close'])

const formData = ref({
	milestone_name: '',
	milestone_date: '',
	description: '',
	priority: 'Medium',
	status: 'Open',
	color: '#3b82f6'
})

const priorities = ['Low', 'Medium', 'High', 'Urgent']
const statuses = ['Open', 'In Progress', 'Completed', 'Cancelled']

watch(() => props.show, (newVal) => {
	if (newVal) {
		if (props.editMode && props.milestone) {
			formData.value = {
				milestone_name: props.milestone.milestone_name || '',
				milestone_date: props.milestone.milestone_date || '',
				description: props.milestone.description || '',
				priority: props.milestone.priority || 'Medium',
				status: props.milestone.status || 'Open',
				color: props.milestone.color || '#3b82f6'
			}
		} else {
			resetForm()
		}
	}
})

function resetForm() {
	formData.value = {
		milestone_name: '',
		milestone_date: '',
		description: '',
		priority: 'Medium',
		status: 'Open',
		color: '#3b82f6'
	}
}

function handleSave() {
	if (!formData.value.milestone_name.trim()) {
		if (window.frappe) {
			frappe.show_alert({ message: 'Please enter a milestone name', indicator: 'red' })
		}
		return
	}

	const data = { ...formData.value }
	
	// For edit mode, rename field for API
	if (props.editMode) {
		data.new_milestone_name = data.milestone_name
		delete data.milestone_name
	}

	emit('save', data)
}
</script>

<template>
	<Teleport to="body">
		<Transition name="modal-fade">
			<div
				v-if="show"
				class="fixed inset-0 z-50 overflow-y-auto"
				@click.self="$emit('close')"
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
								<Diamond class="w-5 h-5 text-blue-600" />
								<h3 class="text-lg font-semibold text-gray-900">
									{{ editMode ? 'Edit' : 'Create' }} Milestone
								</h3>
							</div>
							<button
								@click="$emit('close')"
								class="text-gray-400 hover:text-gray-600 transition-colors"
							>
								<X class="w-5 h-5" />
							</button>
						</div>

						<!-- Body -->
						<div class="px-6 py-4 space-y-4">
							<!-- Name -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									Name <span class="text-red-500">*</span>
								</label>
								<input
									v-model="formData.milestone_name"
									type="text"
									placeholder="e.g., v1.0 Release"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								/>
							</div>

							<!-- Deadline -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									Target Date
								</label>
								<input
									v-model="formData.milestone_date"
									type="date"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								/>
							</div>

							<!-- Priority & Status Row -->
							<div class="grid grid-cols-2 gap-4">
								<!-- Priority -->
								<div>
									<label class="block text-sm font-medium text-gray-700 mb-1">
										Priority
									</label>
									<select
										v-model="formData.priority"
										class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
									>
										<option v-for="p in priorities" :key="p" :value="p">
											{{ p }}
										</option>
									</select>
								</div>

								<!-- Status (only in edit mode) -->
								<div v-if="editMode">
									<label class="block text-sm font-medium text-gray-700 mb-1">
										Status
									</label>
									<select
										v-model="formData.status"
										class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
									>
										<option v-for="s in statuses" :key="s" :value="s">
											{{ s }}
										</option>
									</select>
								</div>

								<!-- Color -->
								<div :class="{ 'col-span-1': editMode }">
									<label class="block text-sm font-medium text-gray-700 mb-1">
										Color
									</label>
									<div class="flex items-center gap-2">
										<input
											v-model="formData.color"
											type="color"
											class="w-10 h-10 rounded border border-gray-300 cursor-pointer"
										/>
										<span class="text-sm text-gray-500">{{ formData.color }}</span>
									</div>
								</div>
							</div>

							<!-- Description -->
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-1">
									Description
								</label>
								<textarea
									v-model="formData.description"
									rows="3"
									placeholder="What needs to be achieved..."
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
								/>
							</div>
						</div>

						<!-- Footer -->
						<div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-gray-200">
							<button
								@click="$emit('close')"
								class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
							>
								Cancel
							</button>
							<button
								@click="handleSave"
								class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
							>
								{{ editMode ? 'Update' : 'Create' }}
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

.modal-fade-enter-active .relative,
.modal-fade-leave-active .relative {
	transition: transform 0.2s ease;
}

.modal-fade-enter-from .relative,
.modal-fade-leave-to .relative {
	transform: scale(0.95);
}
</style>
