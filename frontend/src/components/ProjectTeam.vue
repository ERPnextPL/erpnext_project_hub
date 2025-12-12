<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import { Users, Plus, X, User } from 'lucide-vue-next'

const props = defineProps({
	projectId: {
		type: String,
		required: true,
	},
})

const store = useTaskStore()
const projectUsers = ref([])
const isOpen = ref(false)
const isAddingUser = ref(false)
const searchQuery = ref('')

onMounted(async () => {
	await loadProjectUsers()
	if (store.availableUsers.length === 0) {
		await store.fetchUsers()
	}
})

// Watch for changes in project team (triggered when user is assigned to task)
watch(() => store.projectTeamRefreshTrigger, async () => {
	await loadProjectUsers()
})

async function loadProjectUsers() {
	projectUsers.value = await store.fetchProjectUsers(props.projectId)
}

const availableToAdd = ref([])
async function openAddUser() {
	console.log('openAddUser called', {
		availableUsers: store.availableUsers.length,
		projectUsers: projectUsers.value.length
	})
	isAddingUser.value = true
	// Filter out users already in project
	const projectUserEmails = projectUsers.value.map(u => u.user)
	availableToAdd.value = store.availableUsers.filter(
		u => !projectUserEmails.includes(u.name)
	)
	console.log('availableToAdd:', availableToAdd.value.length)
}

async function addUser(user) {
	try {
		await store.addProjectUser(props.projectId, user.name)
		await loadProjectUsers()
		isAddingUser.value = false
		searchQuery.value = ''
	} catch (error) {
		console.error('Failed to add user:', error)
	}
}

async function removeUser(userEmail) {
	if (!confirm(`Remove ${userEmail} from project?`)) return
	
	try {
		await store.removeProjectUser(props.projectId, userEmail)
		await loadProjectUsers()
	} catch (error) {
		console.error('Failed to remove user:', error)
	}
}

const filteredAvailable = computed(() => {
	const query = searchQuery.value.toLowerCase()
	return availableToAdd.value.filter(user => 
		user.full_name?.toLowerCase().includes(query) ||
		user.name?.toLowerCase().includes(query)
	)
})

function closeDropdown(e) {
	if (!e.target.closest('.project-team-container')) {
		isOpen.value = false
		isAddingUser.value = false
	}
}

onMounted(() => {
	document.addEventListener('click', closeDropdown)
})
</script>

<template>
	<div class="project-team-container relative">
		<!-- Team button -->
		<button
			@click="isOpen = !isOpen"
			class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
		>
			<Users class="w-4 h-4" />
			<span>Team</span>
			<span v-if="projectUsers.length > 0" class="text-xs text-gray-500">
				({{ projectUsers.length }})
			</span>
		</button>

		<!-- Dropdown -->
		<div
			v-if="isOpen"
			class="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
		>
			<!-- Header -->
			<div class="px-4 py-3 border-b border-gray-200">
				<div class="flex items-center justify-between">
					<h3 class="text-sm font-semibold text-gray-900">Project Team</h3>
					<button
						v-if="!isAddingUser"
						@click.stop="openAddUser"
						class="p-1 rounded hover:bg-gray-100 text-blue-600"
						title="Add user"
					>
						<Plus class="w-4 h-4" />
					</button>
				</div>
			</div>

			<!-- Add user view -->
			<div v-if="isAddingUser" class="p-3">
				<div class="mb-3">
					<input
						v-model="searchQuery"
						type="text"
						placeholder="Search users..."
						class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:border-blue-400"
						@click.stop
					/>
				</div>
				<div class="max-h-60 overflow-y-auto space-y-1">
					<button
						v-for="user in filteredAvailable"
						:key="user.name"
						@click.stop="addUser(user)"
						class="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 rounded flex items-center gap-2"
					>
						<img
							v-if="user.user_image"
							:src="user.user_image"
							class="w-6 h-6 rounded-full"
						/>
						<div v-else class="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center">
							<User class="w-4 h-4 text-gray-500" />
						</div>
						<div class="flex-1 min-w-0">
							<div class="font-medium text-gray-900 truncate">{{ user.full_name }}</div>
							<div class="text-xs text-gray-500 truncate">{{ user.name }}</div>
						</div>
					</button>
					<div v-if="filteredAvailable.length === 0" class="px-3 py-6 text-center text-sm text-gray-500">
						No users available to add
					</div>
				</div>
				<div class="mt-3 pt-3 border-t border-gray-200">
					<button
						@click="isAddingUser = false; searchQuery = ''"
						class="w-full px-3 py-2 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
					>
						Cancel
					</button>
				</div>
			</div>

			<!-- Team members list -->
			<div v-else class="max-h-80 overflow-y-auto">
				<div v-if="projectUsers.length === 0" class="px-4 py-8 text-center text-sm text-gray-500">
					No team members yet
				</div>
				<div v-else class="divide-y divide-gray-100">
					<div
						v-for="user in projectUsers"
						:key="user.user"
						class="px-4 py-3 hover:bg-gray-50 flex items-center gap-3 group"
					>
						<img
							v-if="user.user_image"
							:src="user.user_image"
							class="w-8 h-8 rounded-full"
						/>
						<div v-else class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
							<User class="w-5 h-5 text-gray-500" />
						</div>
						<div class="flex-1 min-w-0">
							<div class="font-medium text-gray-900 truncate">{{ user.full_name }}</div>
							<div class="text-xs text-gray-500 truncate">{{ user.user }}</div>
						</div>
						<button
							@click.stop="removeUser(user.user)"
							class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100 text-red-600"
						>
							<X class="w-4 h-4" />
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
