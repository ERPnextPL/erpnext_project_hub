<script setup>
import { ref, computed } from 'vue'
import { useMyTasksStore } from '../../stores/myTasksStore'
import dayjs from 'dayjs'
import {
	Circle,
	Clock,
	CheckCircle2,
	AlertCircle,
	Flag,
	Calendar,
	Folder,
	ChevronRight,
} from 'lucide-vue-next'

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
})

const store = useMyTasksStore()
const isUpdating = ref(false)

// Status config
const statusConfig = {
	'Open': { icon: Circle, class: 'text-blue-600', bg: 'bg-blue-100', label: 'Otwarte' },
	'Working': { icon: Clock, class: 'text-amber-600', bg: 'bg-amber-100', label: 'W trakcie' },
	'Pending Review': { icon: AlertCircle, class: 'text-purple-600', bg: 'bg-purple-100', label: 'Do przeglądu' },
	'Completed': { icon: CheckCircle2, class: 'text-green-600', bg: 'bg-green-100', label: 'Ukończone' },
	'Overdue': { icon: AlertCircle, class: 'text-red-600', bg: 'bg-red-100', label: 'Spóźnione' },
	'Cancelled': { icon: Circle, class: 'text-gray-400', bg: 'bg-gray-100', label: 'Anulowane' },
}

const priorityConfig = {
	'Urgent': { class: 'text-red-600', label: 'Pilne' },
	'High': { class: 'text-orange-500', label: 'Wysokie' },
	'Medium': { class: 'text-yellow-600', label: 'Średnie' },
	'Low': { class: 'text-gray-500', label: 'Niskie' },
}

const currentStatus = computed(() => {
	return statusConfig[props.task.status] || statusConfig['Open']
})

const currentPriority = computed(() => {
	return priorityConfig[props.task.priority] || priorityConfig['Medium']
})

const formattedDate = computed(() => {
	if (!props.task.exp_end_date) return null
	return dayjs(props.task.exp_end_date).format('DD MMM YYYY')
})

const dateClass = computed(() => {
	if (props.task.is_overdue) return 'text-red-600 font-medium'
	if (!props.task.exp_end_date) return 'text-gray-400'
	
	const today = dayjs().startOf('day')
	const dueDate = dayjs(props.task.exp_end_date).startOf('day')
	const diff = dueDate.diff(today, 'day')
	
	if (diff === 0) return 'text-amber-600 font-medium'
	if (diff <= 3) return 'text-amber-500'
	return 'text-gray-500'
})

async function toggleComplete(e) {
	e.stopPropagation()
	const newStatus = props.task.status === 'Completed' ? 'Open' : 'Completed'
	
	isUpdating.value = true
	try {
		await store.quickUpdateTask(props.task.name, { status: newStatus })
	} finally {
		isUpdating.value = false
	}
}

function openTask() {
	store.selectTask(props.task)
}
</script>

<template>
	<div
		@click="openTask"
		:class="[
			'bg-white rounded-lg border border-gray-200 p-4 active:bg-gray-50 transition-colors',
			task.is_overdue && 'border-l-4 border-l-red-500',
			isUpdating && 'opacity-60'
		]"
	>
		<div class="flex items-start gap-3">
			<!-- Checkbox -->
			<button
				@click="toggleComplete"
				class="flex-shrink-0 mt-0.5 p-0.5"
				:disabled="isUpdating"
			>
				<CheckCircle2 
					:class="[
						'w-6 h-6 transition-colors',
						task.status === 'Completed' ? 'text-green-600' : 'text-gray-300'
					]" 
				/>
			</button>

			<!-- Content -->
			<div class="flex-1 min-w-0">
				<!-- Subject -->
				<h3 
					:class="[
						'font-medium text-gray-900 mb-1',
						task.status === 'Completed' && 'line-through text-gray-400'
					]"
				>
					{{ task.subject }}
				</h3>

				<!-- Meta row -->
				<div class="flex flex-wrap items-center gap-2 text-sm">
					<!-- Project -->
					<div 
						v-if="task.project_name"
						class="flex items-center gap-1 text-gray-500"
					>
						<Folder class="w-3.5 h-3.5" />
						<span class="truncate max-w-[120px]">{{ task.project_name }}</span>
					</div>

					<!-- Status badge -->
					<span 
						:class="[
							'flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
							currentStatus.bg,
							currentStatus.class
						]"
					>
						<component :is="currentStatus.icon" class="w-3 h-3" />
						{{ currentStatus.label }}
					</span>

					<!-- Priority -->
					<span :class="['flex items-center gap-1 text-xs', currentPriority.class]">
						<Flag class="w-3 h-3" />
						{{ currentPriority.label }}
					</span>
				</div>

				<!-- Due date -->
				<div 
					v-if="task.exp_end_date || task.is_overdue"
					:class="['flex items-center gap-1 mt-2 text-sm', dateClass]"
				>
					<Calendar class="w-3.5 h-3.5" />
					<span>{{ formattedDate || 'Brak terminu' }}</span>
					<span 
						v-if="task.is_overdue" 
						class="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded font-medium"
					>
						Spóźnione
					</span>
				</div>
			</div>

			<!-- Arrow -->
			<ChevronRight class="w-5 h-5 text-gray-400 flex-shrink-0" />
		</div>
	</div>
</template>
