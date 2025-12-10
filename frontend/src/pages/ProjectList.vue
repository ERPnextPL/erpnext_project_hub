<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Folder, ChevronRight, Calendar, Users } from 'lucide-vue-next'

const router = useRouter()
const projects = ref([])
const loading = ref(true)

onMounted(async () => {
	try {
		const response = await fetch('/api/method/erpnext_projekt_hub.api.outliner.get_projects', {
			headers: {
				'X-Frappe-CSRF-Token': window.csrf_token,
			},
		})
		const data = await response.json()
		projects.value = data.message || []
	} catch (error) {
		console.error('Failed to fetch projects:', error)
	} finally {
		loading.value = false
	}
})

function openProject(projectId) {
	router.push({ name: 'ProjectOutliner', params: { projectId } })
}

function getStatusClass(status) {
	const classes = {
		Open: 'bg-blue-100 text-blue-800',
		Completed: 'bg-green-100 text-green-800',
		Cancelled: 'bg-gray-100 text-gray-600',
	}
	return classes[status] || 'bg-gray-100 text-gray-600'
}
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-10">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<Folder class="w-6 h-6 text-blue-600" />
						<h1 class="text-xl font-semibold text-gray-900">Project Outliner</h1>
					</div>
					<a
						href="/app"
						class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
					>
						← Back to Desk
					</a>
				</div>
			</div>
		</header>

		<!-- Content -->
		<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
			<div class="mb-6">
				<h2 class="text-lg font-medium text-gray-900">All Projects</h2>
				<p class="text-sm text-gray-500">Select a project to manage its tasks</p>
			</div>

			<!-- Loading state -->
			<div v-if="loading" class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			</div>

			<!-- Empty state -->
			<div
				v-else-if="projects.length === 0"
				class="text-center py-12 bg-white rounded-lg border border-gray-200"
			>
				<Folder class="w-12 h-12 text-gray-400 mx-auto mb-4" />
				<h3 class="text-lg font-medium text-gray-900 mb-2">No projects found</h3>
				<p class="text-gray-500">Create a project in ERPNext to get started.</p>
			</div>

			<!-- Project grid -->
			<div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				<div
					v-for="project in projects"
					:key="project.name"
					@click="openProject(project.name)"
					class="bg-white rounded-lg border border-gray-200 p-5 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
				>
					<div class="flex items-start justify-between mb-3">
						<div class="flex items-center gap-2">
							<Folder class="w-5 h-5 text-blue-600" />
							<h3 class="font-medium text-gray-900 group-hover:text-blue-600">
								{{ project.project_name }}
							</h3>
						</div>
						<ChevronRight
							class="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors"
						/>
					</div>

					<div class="space-y-2">
						<div class="flex items-center gap-2 text-sm text-gray-500">
							<span :class="['px-2 py-0.5 rounded-full text-xs font-medium', getStatusClass(project.status)]">
								{{ project.status }}
							</span>
							<span v-if="project.percent_complete !== null" class="text-gray-400">
								{{ project.percent_complete }}% complete
							</span>
						</div>

						<div v-if="project.expected_end_date" class="flex items-center gap-1.5 text-sm text-gray-500">
							<Calendar class="w-4 h-4" />
							<span>Due {{ project.expected_end_date }}</span>
						</div>

						<div class="flex items-center gap-1.5 text-sm text-gray-500">
							<Users class="w-4 h-4" />
							<span>{{ project.task_count || 0 }} tasks</span>
						</div>
					</div>
				</div>
			</div>
		</main>
	</div>
</template>
