/**
 * Tab System Exports
 *
 * Central export point for the Tab Registry system
 */

// Re-export everything from tabRegistry
export {
	default as tabRegistry,
	registerTab,
	unregisterTab,
	getTabs,
	getNavItems,
	getRoutes,
	getReservedSegments,
	getTab,
	getTabByRouteName,
} from '../tabRegistry';

// Export core tabs registration
export { registerCoreTabs } from './coreTabs';

// Note: proTabs is an example file and should not be imported directly
// PRO version apps should create their own proTabs.js based on proTabs.example.js
