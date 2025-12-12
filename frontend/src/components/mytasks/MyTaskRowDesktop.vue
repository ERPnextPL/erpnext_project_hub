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
	ChevronDown,
	Folder,
} from 'lucide-vue-next'

const props = defineProps({
	task: {
		type: Object,
		required: true,
	},
})

const store = useMyTasksStore()

const showStatusDropdown = ref(false)
const showPriorityDropdown = ref(false)
const isUpdating = ref(false)

// Status config - shorter labels to fit in grid
const statusConfig = {
	'Open': { icon: Circle, class: 'text-blue-600', bg: 'bg-blue-100', label: 'Otwarte' },
	'Working': { icon: Clock, class: 'text-amber-600', bg: 'bg-amber-100', label: 'W trakcie' },
	'Pending Review': { icon: AlertCircle, class: 'text-purple-600', bg: 'bg-purple-100', label: 'Przegląd' },
	'Completed': { icon: CheckCircle2, class: 'text-green-600', bg: 'bg-green-100', label: 'Gotowe' },
	'Overdue': { icon: AlertCircle, class: 'text-red-600', bg: 'bg-red-100', label: 'Spóźnione' },
	'Cancelled': { icon: Circle, class: 'text-gray-400', bg: 'bg-gray-100', label: 'Anulowane' },
}

const priorityConfig = {
	'Urgent': { class: 'text-red-600', bg: 'bg-red-100', label: 'Pilne' },
	'High': { class: 'text-orange-500', bg: 'bg-orange-100', label: 'Wysokie' },
	'Medium': { class: 'text-yellow-600', bg: 'bg-yellow-100', label: 'Średnie' },
	'Low': { class: 'text-gray-500', bg: 'bg-gray-100', label: 'Niskie' },
}

const currentStatus = computed(() => {
	return statusConfig[props.task.status] || statusConfig['Open']
})

const currentPriority = computed(() => {
	return priorityConfig[props.task.priority] || priorityConfig['Medium']
})

const formattedDate = computed(() => {
	if (!props.task.exp_end_date) return null
	return dayjs(props.task.exp_end_date).format('DD MMM')
})

const dateClass = computed(() => {
	if (props.task.is_overdue) return 'text-red-600 font-medium'
	if (!props.task.exp_end_date) return 'text-gray-400'
	
	const today = dayjs().startOf('day')
	const dueDate = dayjs(props.task.exp_end_date).startOf('day')
	const diff = dueDate.diff(today, 'day')
	
	if (diff === 0) return 'text-amber-600 font-medium'
	if (diff <= 3) return 'text-amber-500'
	return 'text-gray-600'
})

async function updateStatus(newStatus) {
	showStatusDropdown.value = false
	if (newStatus === props.task.status) return
	
	isUpdating.value = true
	try {
		await store.quickUpdateTask(props.task.name, { status: newStatus })
	} finally {
		isUpdating.value = false
	}
}

async function updatePriority(newPriority) {
	showPriorityDropdown.value = false
	if (newPriority === props.task.priority) return
	
	isUpdating.value = true
	try {
		await store.quickUpdateTask(props.task.name, { priority: newPriority })
	} finally {
		isUpdating.value = false
	}
}

function openTask() {
	store.selectTask(props.task)
}

function closeDropdowns(e) {
	if (!e.target.closest('.status-dropdown')) {
		showStatusDropdown.value = false
	}
	if (!e.target.closest('.priority-dropdown')) {
		showPriorityDropdown.value = false
	}
}
</script>

<template>
	<div
		@click="openTask"
		:class="[
			'grid grid-cols-12 gap-4 px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors items-center',
			isUpdating && 'opacity-60'
		]"
	>
		<!-- Task subject -->
		<div class="col-span-4 flex items-center gap-3 min-w-0">
			<button
				@click.stop="updateStatus(task.status === 'Completed' ? 'Open' : 'Completed')"
				class="flex-shrink-0 p-0.5 rounded hover:bg-gray-100 transition-colors"
				:title="task.status === 'Completed' ? 'Oznacz jako otwarte' : 'Oznacz jako ukończone'"
			>
				<CheckCircle2 
					:class="[
						'w-5 h-5 transition-colors',
						task.status === 'Completed' ? 'text-green-600' : 'text-gray-300 hover:text-gray-400'
					]" 
				/>
			</button>
			<span 
				:class="[
					'truncate',
					task.status === 'Completed' && 'line-through text-gray-400'
				]"
			>
				{{ task.subject }}
			</span>
		</div>

		<!-- Project -->
		<div class="col-span-2 flex items-center min-w-0">
			<div 
				v-if="task.project_name"
				class="flex items-center gap-1.5 text-sm text-gray-500 truncate"
			>
				<Folder class="w-3.5 h-3.5 flex-shrink-0" />
				<span class="truncate">{{ task.project_name }}</span>
			</div>
			<span v-else class="text-gray-300">—</span>
		</div>

		<!-- Status -->
		<div class="col-span-2 flex items-center relative status-dropdown" @click.stop>
			<button
				@click="showStatusDropdown = !showStatusDropdown"
				:class="[
					'flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium transition-colors',
					currentStatus.bg,
					currentStatus.class
				]"
			>
				<component :is="currentStatus.icon" class="w-3.5 h-3.5" />
				{{ currentStatus.label }}
				<ChevronDown class="w-3 h-3" />
			</button>

			<!-- Status dropdown -->
			<Transition name="fade">
				<div
					v-if="showStatusDropdown"
					class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20 min-w-[140px]"
				>
					<button
						v-for="(config, status) in statusConfig"
						:key="status"
						@click="updateStatus(status)"
						:class="[
							'w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left hover:bg-gray-50',
							task.status === status && 'bg-gray-50'
						]"
					>
						<component :is="config.icon" :class="['w-4 h-4', config.class]" />
						{{ config.label }}
					</button>
				</div>
			</Transition>
		</div>

		<!-- Priority -->
		<div class="col-span-2 flex items-center relative priority-dropdown" @click.stop>
			<button
				@click="showPriorityDropdown = !showPriorityDropdown"
				:class="[
					'flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors hover:bg-gray-100',
					currentPriority.class
				]"
				:title="currentPriority.label"
			>
				<Flag class="w-3.5 h-3.5" />
				<ChevronDown class="w-3 h-3" />
			</button>

			<!-- Priority dropdown -->
			<Transition name="fade">
				<div
					v-if="showPriorityDropdown"
					class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20 min-w-[120px]"
				>
					<button
						v-for="(config, priority) in priorityConfig"
						:key="priority"
						@click="updatePriority(priority)"
						:class="[
							'w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left hover:bg-gray-50',
							task.priority === priority && 'bg-gray-50'
						]"
					>
						<Flag :class="['w-4 h-4', config.class]" />
						{{ config.label }}
					</button>
				</div>
			</Transition>
		</div>

		<!-- Due date -->
		<div class="col-span-2 flex items-center" @click.stop>
			<div :class="['flex items-center gap-1.5 text-sm', dateClass]">
				<Calendar class="w-3.5 h-3.5" />
				<span v-if="formattedDate">{{ formattedDate }}</span>
				<span v-else class="text-gray-300">Brak terminu</span>
				<span 
					v-if="task.is_overdue" 
					class="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded"
				>
					!
				</span>
			</div>
		</div>
	</div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
