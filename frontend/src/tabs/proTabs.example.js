/**
 * PRO tabs registration example
 *
 * This file demonstrates how to register additional tabs from a PRO version app.
 * To use this:
 * 1. Copy this file to your PRO app (e.g., erpnext_projekt_hub_pro)
 * 2. Rename it to proTabs.js
 * 3. Import and call registerProTabs() in your main.js before the router is created
 *
 * Example integration in PRO app:
 *
 * // In your PRO app's main.js or plugin initialization:
 * import { registerProTabs } from 'erpnext_projekt_hub_pro/tabs/proTabs';
 * registerProTabs();
 */

import { registerTab } from '../tabRegistry';
import { Users, Clock } from 'lucide-vue-next';

/**
 * Register PRO-only tabs
 */
export function registerProTabs() {
	// Team Manager tab (PRO only)
	registerTab({
		key: 'team',
		routeName: 'TeamManager',
		path: '/project-hub/team-manager',
		labelKey: 'Team',
		icon: Users,
		color: 'text-purple-600',
		bg: 'bg-purple-50',
		component: () => import('../pages/TeamManager.vue'),
		order: 40,
	});

	// Time Management tab (PRO only)
	registerTab({
		key: 'time',
		routeName: 'TimeManagement',
		path: '/project-hub/time-management',
		labelKey: 'Time',
		icon: Clock,
		color: 'text-emerald-600',
		bg: 'bg-emerald-50',
		component: () => import('../pages/TimeManagement.vue'),
		order: 50,
	});

	console.log('PRO tabs registered successfully');
}

/**
 * Alternative: Register tabs conditionally based on license
 */
export function registerProTabsConditional() {
	// Check if user has PRO license (example - adjust to your licensing system)
	const hasPROLicense = window.frappe?.boot?.has_pro_license || false;

	if (hasPROLicense) {
		registerProTabs();
	} else {
		console.log('PRO license not detected, PRO tabs not registered');
	}
}
