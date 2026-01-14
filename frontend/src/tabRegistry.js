/**
 * Tab Registry - Extension point system for Project Hub tabs
 *
 * This allows external apps (like PRO version) to register additional tabs
 * without modifying the core codebase.
 *
 * Usage:
 * import { registerTab } from './tabRegistry';
 *
 * registerTab({
 *   key: 'team',
 *   routeName: 'TeamManager',
 *   path: '/project-hub/team-manager',
 *   labelKey: 'Team',
 *   icon: Users,
 *   color: 'text-purple-600',
 *   bg: 'bg-purple-50',
 *   component: () => import('./pages/TeamManager.vue'),
 *   order: 40 // Optional: controls position in navigation
 * });
 */

class TabRegistry {
	constructor() {
		this.tabs = new Map();
		this.initialized = false;
	}

	/**
	 * Register a new tab
	 * @param {Object} tabConfig - Tab configuration
	 * @param {string} tabConfig.key - Unique key for the tab
	 * @param {string} tabConfig.routeName - Vue Router route name
	 * @param {string} tabConfig.path - URL path for the tab
	 * @param {string} tabConfig.labelKey - Translation key for tab label
	 * @param {Component} tabConfig.icon - Lucide icon component
	 * @param {string} tabConfig.color - Tailwind color class for active state
	 * @param {string} tabConfig.bg - Tailwind background class for active state
	 * @param {Function} tabConfig.component - Vue component lazy loader
	 * @param {number} [tabConfig.order=50] - Sort order (lower numbers appear first)
	 */
	registerTab(tabConfig) {
		if (!tabConfig.key) {
			console.error('Tab registration failed: key is required', tabConfig);
			return;
		}

		if (this.tabs.has(tabConfig.key)) {
			console.warn(`Tab with key "${tabConfig.key}" is already registered. Overwriting.`);
		}

		// Set default order if not provided
		const tab = {
			...tabConfig,
			order: tabConfig.order ?? 50,
		};

		this.tabs.set(tabConfig.key, tab);
		console.log(`Tab registered: ${tabConfig.key}`, tab);
	}

	/**
	 * Unregister a tab
	 * @param {string} key - Tab key to unregister
	 */
	unregisterTab(key) {
		if (this.tabs.has(key)) {
			this.tabs.delete(key);
			console.log(`Tab unregistered: ${key}`);
		}
	}

	/**
	 * Get all registered tabs sorted by order
	 * @returns {Array} Array of tab configurations
	 */
	getTabs() {
		return Array.from(this.tabs.values()).sort((a, b) => a.order - b.order);
	}

	/**
	 * Get navigation items (subset of tab data for navigation component)
	 * @returns {Array} Array of navigation items
	 */
	getNavItems() {
		return this.getTabs().map(tab => ({
			key: tab.key,
			to: tab.path,
			labelKey: tab.labelKey,
			icon: tab.icon,
			color: tab.color,
			bg: tab.bg,
		}));
	}

	/**
	 * Get Vue Router routes for all registered tabs
	 * @returns {Array} Array of route configurations
	 */
	getRoutes() {
		return this.getTabs().map(tab => ({
			path: tab.path,
			name: tab.routeName,
			component: tab.component,
		}));
	}

	/**
	 * Get reserved project segments (for routing conflicts)
	 * @returns {Object} Map of path segments to route names
	 */
	getReservedSegments() {
		const segments = {};
		this.getTabs().forEach(tab => {
			// Extract the last segment from the path (e.g., "my-tasks" from "/project-hub/my-tasks")
			const segment = tab.path.split('/').pop();
			if (segment && segment !== 'project-hub') {
				segments[segment] = tab.routeName;
			}
		});
		return segments;
	}

	/**
	 * Get tab by key
	 * @param {string} key - Tab key
	 * @returns {Object|undefined} Tab configuration
	 */
	getTab(key) {
		return this.tabs.get(key);
	}

	/**
	 * Get tab by route name
	 * @param {string} routeName - Route name
	 * @returns {Object|undefined} Tab configuration
	 */
	getTabByRouteName(routeName) {
		return this.getTabs().find(tab => tab.routeName === routeName);
	}

	/**
	 * Mark registry as initialized
	 * This can be used to ensure all plugins have loaded before using the registry
	 */
	markInitialized() {
		this.initialized = true;
	}

	/**
	 * Check if registry is initialized
	 * @returns {boolean}
	 */
	isInitialized() {
		return this.initialized;
	}

	/**
	 * Reset the registry (useful for testing)
	 */
	reset() {
		this.tabs.clear();
		this.initialized = false;
	}
}

// Create singleton instance
const tabRegistry = new TabRegistry();

// Export singleton instance and helper functions
export default tabRegistry;

export function registerTab(tabConfig) {
	return tabRegistry.registerTab(tabConfig);
}

export function unregisterTab(key) {
	return tabRegistry.unregisterTab(key);
}

export function getTabs() {
	return tabRegistry.getTabs();
}

export function getNavItems() {
	return tabRegistry.getNavItems();
}

export function getRoutes() {
	return tabRegistry.getRoutes();
}

export function getReservedSegments() {
	return tabRegistry.getReservedSegments();
}

export function getTab(key) {
	return tabRegistry.getTab(key);
}

export function getTabByRouteName(routeName) {
	return tabRegistry.getTabByRouteName(routeName);
}
