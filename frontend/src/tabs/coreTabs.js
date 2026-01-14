/**
 * Core tabs registration
 * These are the default tabs available in the base version
 */
import { registerTab } from '../tabRegistry';
import { Folder, CheckSquare, Timer } from 'lucide-vue-next';

/**
 * Register all core tabs
 */
export function registerCoreTabs() {
	// Projects tab
	registerTab({
		key: 'projects',
		routeName: 'ProjectList',
		path: '/project-hub',
		labelKey: 'Projects',
		icon: Folder,
		color: 'text-blue-600',
		bg: 'bg-blue-50',
		component: () => import('../pages/ProjectList.vue'),
		order: 10,
	});

	// My Tasks tab
	registerTab({
		key: 'tasks',
		routeName: 'MyTasks',
		path: '/project-hub/my-tasks',
		labelKey: 'Tasks',
		icon: CheckSquare,
		color: 'text-blue-500',
		bg: 'bg-blue-50',
		component: () => import('../pages/MyTasks.vue'),
		order: 20,
	});

	// My Time Logs tab
	registerTab({
		key: 'my-time',
		routeName: 'MyTimeLogs',
		path: '/project-hub/my-time-logs',
		labelKey: 'My Time',
		icon: Timer,
		color: 'text-amber-600',
		bg: 'bg-amber-50',
		component: () => import('../pages/MyTimeLogs.vue'),
		order: 30,
	});
}
