import { createRouter, createWebHistory } from "vue-router";
import tabRegistry, { getRoutes, getReservedSegments } from "./tabRegistry";
import { registerCoreTabs } from "./tabs/coreTabs";
import { isProTabsAvailable, loadProTabs } from "./tabs/proLoader";

// Register core tabs
registerCoreTabs();

// Register PRO tabs if the runtime exposes them.
// This avoids a hard build-time dependency on the PRO app bundle.
if (isProTabsAvailable()) {
	await loadProTabs(registerCoreTabs);
}

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
