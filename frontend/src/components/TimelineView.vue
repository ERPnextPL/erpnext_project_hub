<script setup>
import { ref, computed, onMounted } from 'vue'
import { Calendar, ChevronLeft, ChevronRight, Diamond } from 'lucide-vue-next'

const props = defineProps({
	tasks: {
		type: Array,
		required: true,
	},
	projectId: {
		type: String,
		required: true,
	},
})

const emit = defineEmits(['task-click'])

// Timeline state
const viewStartDate = ref(new Date())
const daysToShow = ref(30)

// Status colors
const statusColors = {
	'Open': 'bg-blue-500',
	'Working': 'bg-amber-500',
	'Pending Review': 'bg-purple-500',
	'Completed': 'bg-green-500',
	'Overdue': 'bg-red-500',
	'Cancelled': 'bg-gray-400',
}

// Priority colors for border
const priorityColors = {
	'Urgent': 'border-red-500',
	'High': 'border-orange-500',
	'Medium': 'border-yellow-500',
	'Low': 'border-gray-300',
}

// Get tasks with dates for timeline
const timelineTasks = computed(() => {
	return props.tasks.filter(task => task.exp_start_date || task.exp_end_date)
})

// Generate date headers
const dateHeaders = computed(() => {
	const headers = []
	const start = new Date(viewStartDate.value)
	start.setHours(0, 0, 0, 0)
	
	for (let i = 0; i < daysToShow.value; i++) {
		const date = new Date(start)
		date.setDate(start.getDate() + i)
		headers.push({
			date: date,
			dayOfWeek: date.toLocaleDateString('pl-PL', { weekday: 'short' }),
			dayOfMonth: date.getDate(),
			month: date.toLocaleDateString('pl-PL', { month: 'short' }),
			isWeekend: date.getDay() === 0 || date.getDay() === 6,
			isToday: isSameDay(date, new Date()),
		})
	}
	return headers
})

function isSameDay(d1, d2) {
	return d1.getFullYear() === d2.getFullYear() &&
		d1.getMonth() === d2.getMonth() &&
		d1.getDate() === d2.getDate()
}

// Calculate task bar position and width
function getTaskBarStyle(task) {
	const startDate = new Date(viewStartDate.value)
	startDate.setHours(0, 0, 0, 0)
	const endViewDate = new Date(startDate)
	endViewDate.setDate(startDate.getDate() + daysToShow.value)
	
	const taskStart = task.exp_start_date ? new Date(task.exp_start_date) : null
	const taskEnd = task.exp_end_date ? new Date(task.exp_end_date) : null
	
	// If no dates, skip
	if (!taskStart && !taskEnd) return null
	
	// Calculate effective start and end
	let effectiveStart = taskStart || taskEnd
	let effectiveEnd = taskEnd || taskStart
	
	// Ensure start is before end
	if (effectiveStart > effectiveEnd) {
		[effectiveStart, effectiveEnd] = [effectiveEnd, effectiveStart]
	}
	
	// Check if task is visible in current view
	if (effectiveEnd < startDate || effectiveStart > endViewDate) {
		return null
	}
	
	// Calculate position
	const dayWidth = 100 / daysToShow.value
	const startOffset = Math.max(0, (effectiveStart - startDate) / (1000 * 60 * 60 * 24))
	const endOffset = Math.min(daysToShow.value, (effectiveEnd - startDate) / (1000 * 60 * 60 * 24) + 1)
	
	const left = startOffset * dayWidth
	const width = Math.max((endOffset - startOffset) * dayWidth, dayWidth * 0.5)
	
	return {
		left: `${left}%`,
		width: `${width}%`,
	}
}

function navigatePrev() {
	const newDate = new Date(viewStartDate.value)
	newDate.setDate(newDate.getDate() - 7)
	viewStartDate.value = newDate
}

function navigateNext() {
	const newDate = new Date(viewStartDate.value)
	newDate.setDate(newDate.getDate() + 7)
	viewStartDate.value = newDate
}

function goToToday() {
	viewStartDate.value = new Date()
}

function handleTaskClick(task) {
	emit('task-click', task)
}

onMounted(() => {
	// Start from beginning of current week
	const today = new Date()
	const dayOfWeek = today.getDay()
	const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek // Monday
	today.setDate(today.getDate() + diff)
	viewStartDate.value = today
})
</script>

<template>
	<div class="timeline-view h-full flex flex-col bg-white">
		<!-- Header with navigation -->
		<div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
			<div class="flex items-center gap-2">
				<Calendar class="w-5 h-5 text-blue-600" />
				<h3 class="text-sm font-semibold text-gray-700">Oś czasu</h3>
				<span class="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
					{{ timelineTasks.length }} zadań z datami
				</span>
			</div>
			<div class="flex items-center gap-2">
				<button
					@click="navigatePrev"
					class="p-1.5 rounded hover:bg-gray-200 text-gray-600"
					title="Poprzedni tydzień"
				>
					<ChevronLeft class="w-4 h-4" />
				</button>
				<button
					@click="goToToday"
					class="px-3 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded"
				>
					Dzisiaj
				</button>
				<button
					@click="navigateNext"
					class="p-1.5 rounded hover:bg-gray-200 text-gray-600"
					title="Następny tydzień"
				>
					<ChevronRight class="w-4 h-4" />
				</button>
			</div>
		</div>

		<!-- Timeline content -->
		<div class="flex-1 overflow-auto">
			<!-- Date headers -->
			<div class="sticky top-0 z-10 bg-white border-b border-gray-200">
				<div class="flex">
					<!-- Task name column header -->
					<div class="w-64 flex-shrink-0 px-4 py-2 border-r border-gray-200 bg-gray-50">
						<span class="text-xs font-medium text-gray-500 uppercase">Zadanie</span>
					</div>
					<!-- Date columns -->
					<div class="flex-1 flex">
						<div
							v-for="header in dateHeaders"
							:key="header.date.toISOString()"
							:class="[
								'flex-1 min-w-8 px-1 py-2 text-center border-r border-gray-100',
								header.isWeekend ? 'bg-gray-100' : 'bg-white',
								header.isToday ? 'bg-blue-50' : ''
							]"
						>
							<div class="text-xs text-gray-500">{{ header.dayOfWeek }}</div>
							<div :class="[
								'text-sm font-medium',
								header.isToday ? 'text-blue-600' : 'text-gray-700'
							]">
								{{ header.dayOfMonth }}
							</div>
							<div v-if="header.dayOfMonth === 1" class="text-xs text-gray-400">
								{{ header.month }}
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Task rows -->
			<div v-if="timelineTasks.length === 0" class="flex items-center justify-center py-12 text-gray-500">
				<div class="text-center">
					<Calendar class="w-12 h-12 mx-auto mb-3 text-gray-300" />
					<p class="text-sm">Brak zadań z datami do wyświetlenia</p>
					<p class="text-xs text-gray-400 mt-1">Dodaj daty rozpoczęcia lub zakończenia do zadań</p>
				</div>
			</div>

			<div v-else>
				<div
					v-for="task in timelineTasks"
					:key="task.name"
					class="flex hover:bg-gray-50 border-b border-gray-100 group"
				>
					<!-- Task name -->
					<div 
						class="w-64 flex-shrink-0 px-4 py-3 border-r border-gray-200 cursor-pointer"
						@click="handleTaskClick(task)"
					>
						<div class="flex items-center gap-2">
							<Diamond 
								v-if="task.milestone" 
								class="w-3 h-3 flex-shrink-0 text-amber-500" 
							/>
							<span class="text-sm text-gray-900 truncate group-hover:text-blue-600">
								{{ task.subject }}
							</span>
						</div>
						<div class="flex items-center gap-2 mt-1">
							<span :class="[
								'text-xs px-1.5 py-0.5 rounded',
								statusColors[task.status] ? 'text-white' : 'bg-gray-100 text-gray-600',
								statusColors[task.status] || ''
							]">
								{{ task.status }}
							</span>
							<span v-if="task.exp_start_date" class="text-xs text-gray-400">
								{{ task.exp_start_date }}
							</span>
							<span v-if="task.exp_start_date && task.exp_end_date" class="text-xs text-gray-400">→</span>
							<span v-if="task.exp_end_date" class="text-xs text-gray-400">
								{{ task.exp_end_date }}
							</span>
						</div>
					</div>

					<!-- Timeline bar area -->
					<div class="flex-1 relative py-2">
						<!-- Background grid -->
						<div class="absolute inset-0 flex">
							<div
								v-for="header in dateHeaders"
								:key="'bg-' + header.date.toISOString()"
								:class="[
									'flex-1 border-r border-gray-100',
									header.isWeekend ? 'bg-gray-50' : '',
									header.isToday ? 'bg-blue-50/50' : ''
								]"
							></div>
						</div>

						<!-- Task bar -->
						<div
							v-if="getTaskBarStyle(task)"
							:style="getTaskBarStyle(task)"
							:class="[
								'absolute top-1/2 -translate-y-1/2 h-6 rounded cursor-pointer transition-all',
								'hover:shadow-md hover:scale-y-110',
								statusColors[task.status] || 'bg-gray-400',
								'border-l-4',
								priorityColors[task.priority] || 'border-gray-300'
							]"
							@click="handleTaskClick(task)"
							:title="`${task.subject}\n${task.exp_start_date || ''} - ${task.exp_end_date || ''}`"
						>
							<div class="px-2 py-1 text-xs text-white truncate">
								{{ task.subject }}
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.timeline-view {
	min-height: 400px;
}
</style>
