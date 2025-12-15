<script setup>
import { computed } from 'vue'
import { useMyTasksStore } from '../../stores/myTasksStore'
import MyTaskRowDesktop from './MyTaskRowDesktop.vue'
import MyTaskCardMobile from './MyTaskCardMobile.vue'
import { useWindowSize } from '@vueuse/core'

const store = useMyTasksStore()
const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)

const props = defineProps({
	onOpenTimeLogModal: {
		type: Function,
		required: true,
	},
})

const statusOrder = ['Overdue', 'Open', 'Working', 'Pending Review', 'Completed', 'Cancelled']
const statusLabels = {
	Overdue: 'Spóźnione',
	Open: 'Otwarte',
	Working: 'W trakcie',
	'Pending Review': 'Do przeglądu',
	Completed: 'Ukończone',
	Cancelled: 'Anulowane',
}

const tasksByName = computed(() => {
	const m = new Map()
	for (const t of store.tasks) m.set(t.name, t)
	return m
})

const childrenByParent = computed(() => {
	const m = new Map()
	for (const t of store.tasks) {
		if (!t.parent_task) continue
		if (!m.has(t.parent_task)) m.set(t.parent_task, [])
		m.get(t.parent_task).push(t)
	}
	return m
})

function isExpanded(taskName) {
	return store.expandedParents?.has(taskName)
}

function hasChildren(taskName) {
	return (childrenByParent.value.get(taskName) || []).length > 0
}

function buildHierarchyItems(sectionTasks) {
	const sectionNames = new Set(sectionTasks.map(t => t.name))
	const usedContextParents = new Set()
	const items = []

	for (const t of sectionTasks) {
		if (t.parent_task && !sectionNames.has(t.parent_task)) {
			if (!usedContextParents.has(t.parent_task)) {
				usedContextParents.add(t.parent_task)
				const parent = tasksByName.value.get(t.parent_task)
				items.push({
					type: 'context',
					key: `ctx:${t.parent_task}`,
					name: t.parent_task,
					subject: parent?.subject || t.parent_subject || t.parent_task,
				})
			}
			items.push({ type: 'task', key: t.name, task: t, indent: 1 })
			continue
		}

		if (!t.parent_task || !sectionNames.has(t.parent_task)) {
			items.push({ type: 'task', key: t.name, task: t, indent: 0 })
			if (isExpanded(t.name)) {
				const children = (childrenByParent.value.get(t.name) || []).filter(c => sectionNames.has(c.name))
				for (const c of children) {
					items.push({ type: 'task', key: c.name, task: c, indent: 1 })
				}
			}
		}
	}

	return items
}

const sections = computed(() => {
	const all = store.tasks || []
	if (!store.viewOptions?.groupByStatus) {
		return [{ key: 'all', label: null, tasks: all }]
	}

	const groups = new Map()
	for (const s of statusOrder) groups.set(s, [])
	for (const t of all) {
		const s = t.status || 'Open'
		if (!groups.has(s)) groups.set(s, [])
		groups.get(s).push(t)
	}

	return statusOrder
		.filter(s => (groups.get(s) || []).length > 0)
		.map(s => ({ key: s, label: statusLabels[s] || s, tasks: groups.get(s) || [] }))
})
</script>

<template>
	<div>
		<!-- Task list -->
		<div class="bg-white rounded-lg border border-gray-200 overflow-visible">
			<!-- Table header (desktop only) -->
			<div v-if="!isMobile" class="grid grid-cols-12 gap-4 px-4 py-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wider">
				<div class="col-span-4">Zadanie</div>
				<div class="col-span-2">Projekt</div>
				<div class="col-span-2">Status</div>
				<div class="col-span-2">Priorytet</div>
				<div class="col-span-2">Termin</div>
			</div>
			
			<!-- Task rows -->
			<div class="divide-y divide-gray-100">
				<template v-for="section in sections" :key="section.key">
					<div
						v-if="section.label"
						class="px-4 py-2 text-xs font-semibold text-gray-600 bg-gray-50 border-y border-gray-200"
					>
						{{ section.label }} ({{ section.tasks.length }})
					</div>

					<!-- Desktop: hierarchy + context rows -->
					<div v-if="!isMobile">
						<template
							v-for="item in (store.viewOptions?.showHierarchy ? buildHierarchyItems(section.tasks) : section.tasks.map(t => ({ type: 'task', key: t.name, task: t, indent: 0 })))"
							:key="item.key"
						>
							<div
								v-if="item.type === 'context'"
								class="grid grid-cols-12 gap-4 px-4 py-2 bg-gray-50 text-xs text-gray-600"
							>
								<div class="col-span-12 truncate">↳ {{ item.subject }}</div>
							</div>
							<MyTaskRowDesktop
								v-else
								:task="item.task"
								:indent-level="item.indent"
								:hierarchy-enabled="store.viewOptions?.showHierarchy"
								:has-children="store.viewOptions?.showHierarchy && hasChildren(item.task.name)"
								:is-expanded="store.viewOptions?.showHierarchy && isExpanded(item.task.name)"
								@toggle-expand="store.toggleExpandParent"
								@open-time-log-modal="props.onOpenTimeLogModal"
							/>
						</template>
					</div>

					<!-- Mobile: flat list -->
					<template v-else>
						<MyTaskCardMobile
							v-for="task in section.tasks"
							:key="task.name"
							:task="task"
						/>
					</template>
				</template>
			</div>
		</div>

		<!-- Load more / pagination info -->
		<div v-if="store.tasks.length > 0" class="mt-4 text-center text-sm text-gray-500">
			Wyświetlono {{ store.tasks.length }} z {{ store.total }} zadań
		</div>
	</div>
</template>
