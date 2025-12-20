import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Helper to get CSRF token - Frappe sets frappe.csrf_token in base template
function getCsrfToken() {
	// frappe.csrf_token is set by Frappe's base template automatically
	if (window.frappe && window.frappe.csrf_token && window.frappe.csrf_token !== 'None') {
		return window.frappe.csrf_token
	}
	// Fallback to window.csrf_token if set
	if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') {
		return window.csrf_token
	}
	return ''
}

// Helper for API calls with FormData
async function apiCall(method, params = {}) {
	const csrfToken = getCsrfToken()
	
	const formData = new FormData()
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined) {
			formData.append(key, value)
		}
	})
	
	const response = await fetch(`/api/method/${method}`, {
		method: 'POST',
		headers: {
			'X-Frappe-CSRF-Token': csrfToken,
		},
		body: formData,
	})
	
	const data = await response.json()
	
	// Display server messages if present
	if (data._server_messages && window.frappe) {
		try {
			const messages = JSON.parse(data._server_messages)
			if (Array.isArray(messages)) {
				messages.forEach(msg => {
					try {
						const msgData = JSON.parse(msg)
						if (msgData.message) {
							frappe.show_alert({
								message: msgData.message,
								indicator: msgData.indicator || 'blue'
							})
						}
					} catch (e) {
						// If message is already a string, show it directly
						if (typeof msg === 'string') {
							frappe.show_alert({ message: msg, indicator: 'blue' })
						}
					}
				})
			}
		} catch (e) {
			console.error('Error parsing server messages:', e)
		}
	}
	
	if (!response.ok) {
		const errorMsg = data.exception || data._server_messages || 'API Error'
		if (window.frappe) {
			frappe.show_alert({ message: errorMsg, indicator: 'red' })
		}
		throw new Error(errorMsg)
	}
	return data.message
}

export const useTaskStore = defineStore('tasks', () => {
	// State
	const tasks = ref([])
	const project = ref(null)
	const loading = ref(false)
	const selectedTask = ref(null)
	const expandedTasks = ref(new Set())
	const projectTeamRefreshTrigger = ref(0)
	const projectsSettings = ref(null)

	// Computed - build tree structure
	const taskTree = computed(() => {
		const taskMap = new Map()
		const roots = []

		// First pass: create map
		tasks.value.forEach(task => {
			taskMap.set(task.name, { ...task, children: [] })
		})

		// Second pass: build tree
		tasks.value.forEach(task => {
			const node = taskMap.get(task.name)
			if (task.parent_task && taskMap.has(task.parent_task)) {
				taskMap.get(task.parent_task).children.push(node)
			} else {
				roots.push(node)
			}
		})

		// Sort by idx
		const sortByIdx = (a, b) => (a.idx || 0) - (b.idx || 0)
		const sortTree = (nodes) => {
			nodes.sort(sortByIdx)
			nodes.forEach(node => {
				if (node.children.length > 0) {
					sortTree(node.children)
				}
			})
		}
		sortTree(roots)

		return roots
	})

	// Flatten tree for display (respecting expanded state)
	const flattenedTasks = computed(() => {
		const result = []
		const flatten = (nodes, level = 0) => {
			nodes.forEach(node => {
				result.push({ ...node, level })
				if (node.children.length > 0 && expandedTasks.value.has(node.name)) {
					flatten(node.children, level + 1)
				}
			})
		}
		flatten(taskTree.value)
		return result
	})

	// Actions
	async function fetchTasks(projectId) {
		loading.value = true
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_project_tasks', {
				project: projectId
			})
			if (data) {
				tasks.value = data.tasks || []
				project.value = data.project || null
				// Expand all by default
				tasks.value.forEach(t => {
					if (t.is_group) expandedTasks.value.add(t.name)
				})
			}
		} catch (error) {
			console.error('Failed to fetch tasks:', error)
		} finally {
			loading.value = false
		}
	}

	async function createTask(taskData) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.create_task', taskData)
			if (data) {
				tasks.value.push(data)
				// Refresh project to update percent_complete
				if (project.value) {
					await refreshProject()
				}
				return data
			}
		} catch (error) {
			console.error('Failed to create task:', error)
			throw error
		}
	}

	async function updateTask(taskName, updates) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.update_task', {
				task_name: taskName,
				...updates
			})
			if (data) {
				const index = tasks.value.findIndex(t => t.name === taskName)
				
				// Check if trying to complete but status didn't change (has incomplete subtasks)
				if (updates.status === 'Completed' && data.status !== 'Completed') {
					// Find incomplete subtasks
					const findSubtasks = (parentName) => {
						const subtasks = []
						tasks.value.forEach(task => {
							if (task.parent_task === parentName) {
								subtasks.push(task)
								subtasks.push(...findSubtasks(task.name))
							}
						})
						return subtasks
					}
					
					const subtasks = findSubtasks(taskName)
					const incompleteSubtasks = subtasks.filter(t => 
						t.status !== 'Completed' && t.status !== 'Cancelled'
					)
					
					if (window.frappe && incompleteSubtasks.length > 0) {
						const subtaskNames = incompleteSubtasks.slice(0, 3).map(t => t.subject).join(', ')
						const moreCount = incompleteSubtasks.length > 3 ? ` and ${incompleteSubtasks.length - 3} more` : ''
						frappe.show_alert({ 
							message: `Cannot complete task. ${incompleteSubtasks.length} subtask(s) are not completed: ${subtaskNames}${moreCount}`, 
							indicator: 'blue' 
						})
					}
				}
				
				if (index !== -1) {
					tasks.value[index] = { ...tasks.value[index], ...data }
				}
				// Refresh project data if status changed (affects percent_complete)
				if (updates.status && data.status === updates.status && project.value) {
					await refreshProject()
					// Also refresh milestones if task has milestone assigned
					const task = tasks.value[index]
					if (task && task.milestone) {
						await fetchMilestones(project.value.name)
					}
				}
				return data
			}
		} catch (error) {
			console.error('Failed to update task:', error)
			throw error
		}
	}
	
	async function refreshProject() {
		if (!project.value) return
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_project_tasks', {
				project: project.value.name
			})
			if (data && data.project) {
				project.value = data.project
			}
		} catch (error) {
			console.error('Failed to refresh project:', error)
		}
	}

	async function updateProject(projectName, updates) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.update_project', {
				project: projectName,
				...updates,
			})
			if (data) {
				project.value = { ...(project.value || {}), ...data }
				return data
			}
		} catch (error) {
			console.error('Failed to update project:', error)
			throw error
		}
	}

	async function deleteTask(taskName) {
		try {
			await apiCall('erpnext_projekt_hub.api.outliner.delete_task', {
				task_name: taskName
			})
			tasks.value = tasks.value.filter(t => t.name !== taskName)
			// Refresh project to update percent_complete
			if (project.value) {
				await refreshProject()
			}
		} catch (error) {
			console.error('Failed to delete task:', error)
			throw error
		}
	}

	async function reorderTask(taskName, newParent, newIdx) {
		try {
			await apiCall('erpnext_projekt_hub.api.outliner.reorder_task', {
				task_name: taskName,
				parent_task: newParent,
				idx: newIdx
			})
			// Refetch to get updated tree
			if (project.value) {
				await fetchTasks(project.value.name)
			}
		} catch (error) {
			console.error('Failed to reorder task:', error)
			throw error
		}
	}

	function toggleExpand(taskName) {
		if (expandedTasks.value.has(taskName)) {
			expandedTasks.value.delete(taskName)
		} else {
			expandedTasks.value.add(taskName)
		}
	}

	function expandAll() {
		tasks.value.forEach(t => {
			if (t.is_group) expandedTasks.value.add(t.name)
		})
	}

	function collapseAll() {
		expandedTasks.value.clear()
	}

	function selectTask(task) {
		selectedTask.value = task
	}

	function clearSelection() {
		selectedTask.value = null
	}

	// All projects for task project change
	const allProjects = ref([])

	async function fetchAllProjects() {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_all_projects', {})
			allProjects.value = data || []
			return data
		} catch (error) {
			console.error('Failed to fetch all projects:', error)
			return []
		}
	}

	// User assignment functions
	const availableUsers = ref([])

	async function fetchUsers() {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_users', {})
			availableUsers.value = data || []
		} catch (error) {
			console.error('Failed to fetch users:', error)
		}
	}

	async function fetchProjectsSettings() {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_projects_settings', {})
			projectsSettings.value = data || {}
			return data
		} catch (error) {
			console.error('Failed to fetch projects settings:', error)
			projectsSettings.value = {}
			return {}
		}
	}

	async function assignTask(taskName, user, action = 'add') {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.assign_task', {
				task_name: taskName,
				user: user,
				action: action
			})
			if (data) {
				const index = tasks.value.findIndex(t => t.name === taskName)
				if (index !== -1) {
					tasks.value[index]._assign = data._assign
				}
				// Update selected task if it's the same
				if (selectedTask.value?.name === taskName) {
					selectedTask.value._assign = data._assign
				}
				// Trigger project team refresh
				projectTeamRefreshTrigger.value++
			}
			return data
		} catch (error) {
			console.error('Failed to assign task:', error)
			throw error
		}
	}

	async function fetchProjectUsers(projectName) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_project_users', {
				project: projectName
			})
			return data || []
		} catch (error) {
			console.error('Failed to fetch project users:', error)
			return []
		}
	}

	async function addProjectUser(projectName, user) {
		try {
			await apiCall('erpnext_projekt_hub.api.outliner.add_project_user', {
				project: projectName,
				user: user
			})
			return true
		} catch (error) {
			console.error('Failed to add project user:', error)
			throw error
		}
	}

	async function removeProjectUser(projectName, user) {
		try {
			await apiCall('erpnext_projekt_hub.api.outliner.remove_project_user', {
				project: projectName,
				user: user
			})
			return true
		} catch (error) {
			console.error('Failed to remove project user:', error)
			throw error
		}
	}

	// Time log functions
	const taskTimelogs = ref({})
	const activityTypes = ref([])
	const taskStatuses = ref([])
	const taskPriorities = ref([])

	// Milestone state
	const milestones = ref([])
	const activeMilestoneFilter = ref(null)

	async function fetchActivityTypes() {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_activity_types', {})
			activityTypes.value = data || []
			return data
		} catch (error) {
			console.error('Failed to fetch activity types:', error)
			// Fallback to default types if API fails
			activityTypes.value = ['Execution', 'Communication', 'Planning', 'Research', 'Testing', 'Documentation', 'Meeting', 'Training']
			return activityTypes.value
		}
	}

	async function fetchTaskStatuses() {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_task_statuses', {})
			taskStatuses.value = data || []
			return data
		} catch (error) {
			console.error('Failed to fetch task statuses:', error)
			// Fallback to default statuses if API fails
			taskStatuses.value = ['Open', 'Working', 'Pending Review', 'Completed', 'Overdue', 'Cancelled']
			return taskStatuses.value
		}
	}

	async function fetchTaskPriorities() {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_task_priorities', {})
			taskPriorities.value = data || []
			return data
		} catch (error) {
			console.error('Failed to fetch task priorities:', error)
			// Fallback to default priorities if API fails
			taskPriorities.value = ['Low', 'Medium', 'High', 'Urgent']
			return taskPriorities.value
		}
	}

	async function fetchTaskTimelogs(taskName) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_task_timelogs', {
				task_name: taskName
			})
			taskTimelogs.value[taskName] = data
			return data
		} catch (error) {
			console.error('Failed to fetch task timelogs:', error)
			throw error
		}
	}

	async function createTimelog(timelogData) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.create_timelog', timelogData)
			// Refresh timelogs for this task
			if (timelogData.task) {
				await fetchTaskTimelogs(timelogData.task)
			}
			return data
		} catch (error) {
			console.error('Failed to create timelog:', error)
			throw error
		}
	}

	async function updateTimelog(timelogName, updates) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.update_timelog', {
				timelog_name: timelogName,
				...updates
			})
			return data
		} catch (error) {
			console.error('Failed to update timelog:', error)
			throw error
		}
	}

	async function deleteTimelog(timelogName, taskName) {
		try {
			await apiCall('erpnext_projekt_hub.api.outliner.delete_timelog', {
				timelog_name: timelogName
			})
			// Refresh timelogs for this task
			if (taskName) {
				await fetchTaskTimelogs(taskName)
			}
			return true
		} catch (error) {
			console.error('Failed to delete timelog:', error)
			throw error
		}
	}

	// ==========================================================================
	// MILESTONE FUNCTIONS
	// ==========================================================================

	async function fetchMilestones(projectName) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.get_project_milestones', {
				project: projectName
			})
			milestones.value = data || []
			return data
		} catch (error) {
			console.error('Failed to fetch milestones:', error)
			milestones.value = []
			throw error
		}
	}

	async function createMilestone(milestoneData) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.create_milestone', milestoneData)
			// Refresh milestones list
			if (milestoneData.project) {
				await fetchMilestones(milestoneData.project)
			}
			return data
		} catch (error) {
			console.error('Failed to create milestone:', error)
			throw error
		}
	}

	async function updateMilestone(milestoneName, updates) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.update_milestone', {
				milestone_name: milestoneName,
				...updates
			})
			// Refresh milestones list
			if (project.value?.name) {
				await fetchMilestones(project.value.name)
			}
			return data
		} catch (error) {
			console.error('Failed to update milestone:', error)
			throw error
		}
	}

	async function deleteMilestone(milestoneName) {
		try {
			await apiCall('erpnext_projekt_hub.api.outliner.delete_milestone', {
				milestone_name: milestoneName
			})
			// Refresh milestones and tasks
			if (project.value?.name) {
				await fetchMilestones(project.value.name)
				await fetchTasks(project.value.name)
			}
			// Clear filter if deleted milestone was active
			if (activeMilestoneFilter.value === milestoneName) {
				activeMilestoneFilter.value = null
			}
			return true
		} catch (error) {
			console.error('Failed to delete milestone:', error)
			throw error
		}
	}

	async function assignTaskToMilestone(taskName, milestoneName) {
		try {
			const data = await apiCall('erpnext_projekt_hub.api.outliner.assign_task_to_milestone', {
				task_name: taskName,
				milestone: milestoneName || ''
			})
			// Refresh data
			if (project.value?.name) {
				await fetchMilestones(project.value.name)
				await fetchTasks(project.value.name)
			}
			return data
		} catch (error) {
			console.error('Failed to assign task to milestone:', error)
			throw error
		}
	}

	// Computed: tasks filtered by active milestone
	const tasksFilteredByMilestone = computed(() => {
		if (!activeMilestoneFilter.value) {
			return tasks.value
		}
		return tasks.value.filter(task => task.milestone === activeMilestoneFilter.value)
	})

	// Computed: task tree filtered by milestone
	const taskTreeFilteredByMilestone = computed(() => {
		if (!activeMilestoneFilter.value) {
			return taskTree.value
		}

		// Get all tasks that match the milestone or have children that match
		const matchingTaskNames = new Set()
		
		// First, find all tasks that directly match
		tasks.value.forEach(task => {
			if (task.milestone === activeMilestoneFilter.value) {
				matchingTaskNames.add(task.name)
				// Also add all parent tasks
				let parentName = task.parent_task
				while (parentName) {
					matchingTaskNames.add(parentName)
					const parentTask = tasks.value.find(t => t.name === parentName)
					parentName = parentTask?.parent_task
				}
			}
		})

		// Filter the tree
		const filterTree = (nodes) => {
			return nodes
				.filter(node => matchingTaskNames.has(node.name))
				.map(node => ({
					...node,
					children: filterTree(node.children)
				}))
		}

		return filterTree(taskTree.value)
	})

	function setMilestoneFilter(milestoneName) {
		activeMilestoneFilter.value = milestoneName
	}

	function clearMilestoneFilter() {
		activeMilestoneFilter.value = null
	}

	return {
		// State
		tasks,
		project,
		loading,
		selectedTask,
		expandedTasks,
		availableUsers,
		allProjects,
		taskTimelogs,
		activityTypes,
		taskStatuses,
		taskPriorities,
		milestones,
		activeMilestoneFilter,
		projectTeamRefreshTrigger,
		projectsSettings,
		// Computed
		taskTree,
		flattenedTasks,
		tasksFilteredByMilestone,
		taskTreeFilteredByMilestone,
		// Actions
		fetchTasks,
		createTask,
		updateTask,
		updateProject,
		deleteTask,
		reorderTask,
		toggleExpand,
		expandAll,
		collapseAll,
		selectTask,
		clearSelection,
		// User assignment
		fetchUsers,
		assignTask,
		fetchProjectUsers,
		addProjectUser,
		removeProjectUser,
		// Projects
		fetchAllProjects,
		fetchProjectsSettings,
		// Metadata
		fetchActivityTypes,
		fetchTaskStatuses,
		fetchTaskPriorities,
		// Time logs
		fetchTaskTimelogs,
		createTimelog,
		updateTimelog,
		deleteTimelog,
		// Milestones
		fetchMilestones,
		createMilestone,
		updateMilestone,
		deleteMilestone,
		assignTaskToMilestone,
		setMilestoneFilter,
		clearMilestoneFilter,
	}
})
