import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/outliner',
		name: 'ProjectList',
		component: () => import('./pages/ProjectList.vue'),
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
