import { createRouter, createWebHistory } from "vue-router";
import tabRegistry, { getRoutes, getReservedSegments } from "./tabRegistry";
import { registerCoreTabs } from "./tabs/coreTabs";
import { registerProTabs } from "virtual:pro-tabs";

// Register core tabs
registerCoreTabs();

// Register PRO tabs from projekt_hub_pro.
// "virtual:pro-tabs" is a Vite virtual module defined in vite.config.js.
// At build time it checks if projekt_hub_pro is installed:
//   - If yes: re-exports registerProTabs from the PRO app
//   - If no: exports a noop function (no tabs registered)
registerProTabs();

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
