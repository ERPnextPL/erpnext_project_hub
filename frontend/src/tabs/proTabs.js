/**
 * Pro tabs registration
 * These are additional tabs available in projekt_hub_pro
 */
import { registerTab } from '../tabRegistry';
import { CalendarDays } from 'lucide-vue-next';

/**
 * Register all pro tabs
 */
export function registerProTabs() {
	// Weekly Planner tab
	registerTab({
		key: 'weekly-planner',
		routeName: 'WeeklyPlanner',
		path: '/project-hub/weekly-planner',
		labelKey: 'Weekly Planner',
		icon: CalendarDays,
		color: 'text-purple-600',
		bg: 'bg-purple-50',
		component: () => import('../pages/WeeklyPlanner.vue'),
		order: 25, // Between My Tasks (20) and My Time (30)
	});
}
