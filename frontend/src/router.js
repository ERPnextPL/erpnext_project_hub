import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/project-hub',
		name: 'ProjectList',
		component: () => import('./pages/ProjectList.vue'),
	},
	{
		path: '/project-hub/my-tasks',
		name: 'MyTasks',
		component: () => import('./pages/MyTasks.vue'),
	},
	{
		path: '/project-hub/team-manager',
		name: 'TeamManager',
		component: () => import('./pages/TeamManager.vue'),
	},
	{
		path: '/project-hub/time-management',
		name: 'TimeManagement',
		component: () => import('./pages/TimeManagement.vue'),
	},
	{
		path: '/project-hub/:projectId',
		name: 'ProjectOutliner',
		component: () => import('./pages/ProjectOutliner.vue'),
		props: true,
	},
]

const router = createRouter({
	history: createWebHistory(),
	routes,
})

export default router
