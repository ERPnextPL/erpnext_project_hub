<script setup>
import { ref, onMounted } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import { Plus } from 'lucide-vue-next'

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
	parentTask: {
		type: String,
		default: null,
	},
	milestone: {
		type: String,
		default: null,
	},
	placeholder: {
		type: String,
		default: 'Add a task...',
	},
	autoFocus: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['created', 'cancel'])

const store = useTaskStore()
const inputValue = ref('')
const isCreating = ref(false)
const inputRef = ref(null)

async function createTask() {
	const subject = inputValue.value.trim()
	if (!subject || isCreating.value) return

	isCreating.value = true
	try {
		const parent = props.parentTask ? store.tasks.find(t => t.name === props.parentTask) : null
		if (parent && (parent.status === 'Completed' || parent.status === 'Cancelled')) {
			return
		}

		await store.createTask({
			subject,
			project: props.projectId,
			parent_task: props.parentTask,
			status: parent?.status,
			priority: parent?.priority,
			exp_end_date: parent?.exp_end_date || null,
			// milestone: props.milestone, // if you have milestone field
		})
		inputValue.value = ''
		emit('created')
	} catch (error) {
		console.error('Failed to create task:', error)
	} finally {
		isCreating.value = false
	}
}

function handleKeydown(e) {
	if (e.key === 'Enter' && !e.shiftKey) {
		e.preventDefault()
		createTask()
	} else if (e.key === 'Escape') {
		emit('cancel')
	}
}

onMounted(() => {
	if (props.autoFocus) {
		inputRef.value?.focus()
	}
})
</script>

<template>
	<div class="flex items-center gap-2 px-4 py-2 group">
		<Plus class="w-4 h-4 text-gray-400 flex-shrink-0" />
		<input
			ref="inputRef"
			v-model="inputValue"
			type="text"
			:placeholder="placeholder"
			class="quick-add-input"
			:disabled="isCreating"
			@keydown="handleKeydown"
		/>
		<button
			v-if="inputValue.trim()"
			@click="createTask"
			:disabled="isCreating"
			class="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex-shrink-0"
		>
			{{ isCreating ? 'Adding...' : 'Add' }}
		</button>
	</div>
</template>
