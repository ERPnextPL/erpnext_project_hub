/**
 * Core tabs registration
 * These are the default tabs available in the base version
 */
import { registerTab } from '../tabRegistry';
import { Folder, CheckSquare, Timer, ClipboardList, LayoutGrid } from 'lucide-vue-next';

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

	// All Time Logs tab (manager only)
	registerTab({
		key: 'all-time',
		routeName: 'ManagerTimeLogs',
		path: '/project-hub/all-time-logs',
		labelKey: 'All Time',
		icon: ClipboardList,
		color: 'text-emerald-600',
		bg: 'bg-emerald-50',
		component: () => import('../pages/ManagerTimeLogs.vue'),
		order: 35,
		managerOnly: true,
	});

	// Capacity Planning tab (manager only)
	registerTab({
		key: 'capacity',
		routeName: 'CapacityPlanning',
		path: '/project-hub/capacity-planning',
		labelKey: 'Capacity',
		icon: LayoutGrid,
		color: 'text-purple-600',
		bg: 'bg-purple-50',
		component: () => import('../pages/CapacityPlanning.vue'),
		order: 40,
		managerOnly: true,
	});
}
