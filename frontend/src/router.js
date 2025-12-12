import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/outliner',
		name: 'ProjectList',
		component: () => import('./pages/ProjectList.vue'),
	},
	{
		path: '/outliner/my-tasks',
		name: 'MyTasks',
		component: () => import('./pages/MyTasks.vue'),
	},
	{
		path: '/outliner/team-manager',
		name: 'TeamManager',
		component: () => import('./pages/TeamManager.vue'),
	},
	{
		path: '/outliner/time-management',
		name: 'TimeManagement',
		component: () => import('./pages/TimeManagement.vue'),
	},
	{
		path: '/outliner/:projectId',
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
