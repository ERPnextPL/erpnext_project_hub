import { createRouter, createWebHistory } from "vue-router";
import tabRegistry, { getRoutes, getReservedSegments } from "./tabRegistry";
import { registerCoreTabs } from "./tabs/coreTabs";

// Register core tabs
registerCoreTabs();

// Extension point: PRO version or other plugins can register additional tabs here
// Example:
// import { registerProTabs } from 'erpnext_projekt_hub_pro/tabs/proTabs';
// registerProTabs();

// Mark registry as initialized
tabRegistry.markInitialized();

// Get routes from registry
const tabRoutes = getRoutes();

// Get reserved segments from registry
const RESERVED_PROJECT_SEGMENTS = getReservedSegments();

const routes = [
	// Add all registered tab routes
	...tabRoutes,
	// Project Outliner route (must come last to avoid conflicts)
	{
		path: "/project-hub/:projectId",
		name: "ProjectOutliner",
		component: () => import("./pages/ProjectOutliner.vue"),
		props: true,
		beforeEnter(to) {
			const segment = to.params.projectId;
			if (typeof segment !== "string") return;
			if (RESERVED_PROJECT_SEGMENTS[segment]) {
				return { name: RESERVED_PROJECT_SEGMENTS[segment] };
			}
		},
	},
];

const router = createRouter({
	history: createWebHistory(),
	routes,
});

export default router;
