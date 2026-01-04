<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMyTasksStore } from '../stores/myTasksStore'
import { useDebounceFn } from '@vueuse/core'
import {
	CheckSquare,
	Plus,
	Search,
	Filter,
	X,
	RefreshCw,
	AlertCircle,
	LayoutList,
	LayoutGrid,
} from 'lucide-vue-next'
import OutlinerNav from '../components/OutlinerNav.vue'
import MyTaskFilters from '../components/mytasks/MyTaskFilters.vue'
import MyTaskList from '../components/mytasks/MyTaskList.vue'
import MyTaskDrawer from '../components/mytasks/MyTaskDrawer.vue'
import TimeLogModal from '../components/TimeLogModal.vue'

const router = useRouter()
const store = useMyTasksStore()
const realWindow = typeof globalThis !== 'undefined' ? globalThis.window : undefined
const translate = (text) => {
	return (typeof realWindow !== 'undefined' && typeof realWindow.__ === 'function') ? realWindow.__(text) : text
}

const showFilters = ref(false)
const searchInput = ref('')
const viewMode = ref('list') // 'list' or 'kanban' (TODO)

// Time log modal state
const showTimeLogModal = ref(false)
const selectedTaskForTimeLog = ref(null)

// Debounced search
const debouncedSearch = useDebounceFn((value) => {
	store.setFilter('search', value)
	store.fetchTasks()
}, 300)

watch(searchInput, (value) => {
	debouncedSearch(value)
})

onMounted(async () => {
	await Promise.all([
		store.fetchMetadata(),
		store.fetchProjects(),
	])
	await store.fetchTasks()
})

function handleRetry() {
	store.fetchTasks()
}

function openNewTaskDrawer() {
	store.openNewTask()
}

function handleDrawerClose() {
	store.closeDrawer()
}

function handleTaskCreated() {
	store.closeDrawer()
}

// Time log modal handlers
function openTimeLogModal(task) {
	selectedTaskForTimeLog.value = task
	showTimeLogModal.value = true
}

async function handleTimeLogSave(timelogData) {
	try {
		await store.createTimelog(timelogData)
		showTimeLogModal.value = false
		selectedTaskForTimeLog.value = null
		if (realWindow?.frappe) {
			frappe.show_alert({ message: translate('Time entry saved'), indicator: 'green' })
		}
	} catch (error) {
		if (realWindow?.frappe) {
			frappe.show_alert({ message: translate('Failed to save time entry'), indicator: 'red' })
		}
	}
}

const isMobile = computed(() => {
	if (realWindow) {
		return realWindow.innerWidth < 768
	}
	return false
})
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-20">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<CheckSquare class="w-6 h-6 text-blue-600" />
						<h1 class="text-xl font-semibold text-gray-900">{{ translate('My Tasks') }}</h1>
						<span 
							v-if="store.total > 0" 
							class="text-sm text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full"
						>
							{{ store.total }}
						</span>
					</div>
					<div class="flex items-center gap-3 sm:gap-4">
						<OutlinerNav />
						<a
							href="/app"
							class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 whitespace-nowrap"
						>
							← Back to Desk
						</a>
					</div>
				</div>
			</div>
		</header>

		<!-- Toolbar -->
		<div class="bg-white border-b border-gray-200 sticky top-16 z-10">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
				<div class="flex flex-col sm:flex-row sm:items-center gap-3">
					<!-- Search -->
					<div class="relative flex-1 max-w-md">
						<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
						<input
							v-model="searchInput"
							type="text"
						:placeholder="translate('Search tasks...')"
							class="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						/>
						<button
							v-if="searchInput"
							@click="searchInput = ''; store.setFilter('search', ''); store.fetchTasks()"
							class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
						>
							<X class="w-4 h-4" />
						</button>
					</div>

					<div class="flex items-center gap-2">
						<!-- Filter toggle -->
						<button
							@click="showFilters = !showFilters"
							:class="[
								'flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors',
								showFilters || store.hasActiveFilters
									? 'bg-blue-50 border-blue-200 text-blue-700'
									: 'border-gray-300 text-gray-700 hover:bg-gray-50'
							]"
						>
							<Filter class="w-4 h-4" />
							<span class="hidden sm:inline">{{ translate('Filters') }}</span>
							<span 
								v-if="store.hasActiveFilters" 
								class="w-2 h-2 rounded-full bg-blue-600"
							></span>
						</button>

						<!-- View mode toggle (TODO: Kanban) -->
						<div class="hidden sm:flex items-center border border-gray-300 rounded-lg overflow-hidden">
							<button
								@click="viewMode = 'list'"
								:class="[
									'p-2 transition-colors',
									viewMode === 'list' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:bg-gray-50'
								]"
								:title="translate('List view')"
							>
								<LayoutList class="w-4 h-4" />
							</button>
							<button
								@click="viewMode = 'kanban'"
								:class="[
									'p-2 transition-colors',
									viewMode === 'kanban' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:bg-gray-50'
								]"
								:title="translate('Kanban view (coming soon)')"
								disabled
							>
								<LayoutGrid class="w-4 h-4 opacity-50" />
							</button>
						</div>

						<!-- Refresh -->
						<button
							@click="store.fetchTasks()"
							:disabled="store.loading"
							class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
							:title="translate('Refresh')"
						>
							<RefreshCw :class="['w-4 h-4', store.loading && 'animate-spin']" />
						</button>

						<!-- New task CTA -->
						<button
							@click="openNewTaskDrawer"
							class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
						>
							<Plus class="w-4 h-4" />
							<span class="hidden sm:inline">{{ translate('New Task') }}</span>
						</button>
					</div>
				</div>

				<!-- Filters panel -->
				<Transition name="slide-fade">
					<div v-if="showFilters" class="mt-4 pt-4 border-t border-gray-200">
						<MyTaskFilters />
					</div>
				</Transition>
			</div>
		</div>

		<!-- Content -->
		<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<!-- Loading state -->
			<div v-if="store.loading && store.tasks.length === 0" class="space-y-4">
				<div v-for="i in 5" :key="i" class="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
					<div class="flex items-center gap-4">
						<div class="w-5 h-5 bg-gray-200 rounded"></div>
						<div class="flex-1 space-y-2">
							<div class="h-4 bg-gray-200 rounded w-3/4"></div>
							<div class="h-3 bg-gray-200 rounded w-1/4"></div>
						</div>
						<div class="w-20 h-6 bg-gray-200 rounded"></div>
					</div>
				</div>
			</div>

			<!-- Error state -->
			<div
				v-else-if="store.error"
				class="text-center py-12 bg-white rounded-lg border border-red-200"
			>
				<AlertCircle class="w-12 h-12 text-red-400 mx-auto mb-4" />
				<h3 class="text-lg font-medium text-gray-900 mb-2">{{ translate('Task list failed to load') }}</h3>
				<p class="text-gray-500 mb-4">{{ store.error }}</p>
				<button
					@click="handleRetry"
					class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
				>
					{{ translate('Try again') }}
				</button>
			</div>

			<!-- Empty state -->
			<div
				v-else-if="!store.loading && store.tasks.length === 0"
				class="text-center py-12 bg-white rounded-lg border border-gray-200"
			>
				<CheckSquare class="w-12 h-12 text-gray-400 mx-auto mb-4" />
				<h3 class="text-lg font-medium text-gray-900 mb-2">
					{{ store.hasActiveFilters ? translate('No tasks match the filters') : translate('No tasks assigned yet') }}
				</h3>
				<p class="text-gray-500 mb-4">
					{{ store.hasActiveFilters 
						? translate('Try adjusting the search criteria') 
						: translate('You do not have any tasks assigned yet') 
					}}
				</p>
				<div class="flex items-center justify-center gap-3">
					<button
						v-if="store.hasActiveFilters"
						@click="store.clearFilters(); searchInput = ''"
						class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
					>
						{{ translate('Clear filters') }}
					</button>
					<button
						@click="openNewTaskDrawer"
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
					>
						{{ translate('Create new task') }}
					</button>
				</div>
			</div>

			<!-- Task list -->
			<MyTaskList 
				v-else 
				:on-open-time-log-modal="openTimeLogModal"
			/>
		</main>

		<!-- Task Drawer -->
		<MyTaskDrawer
			:is-open="store.drawerOpen"
			:task="store.selectedTask"
			:is-new="store.drawerMode === 'new'"
			@close="handleDrawerClose"
			@created="handleTaskCreated"
		/>

		<!-- Time Log Modal -->
		<TimeLogModal
			v-if="showTimeLogModal && selectedTaskForTimeLog"
			:task="selectedTaskForTimeLog"
			:show="showTimeLogModal"
			@close="showTimeLogModal = false"
			@save="handleTimeLogSave"
		/>
	</div>
</template>

<style scoped>
.slide-fade-enter-active {
	transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
	transition: all 0.2s ease-in;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
	opacity: 0;
	transform: translateY(-10px);
}
</style>
