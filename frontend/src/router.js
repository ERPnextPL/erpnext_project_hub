import { createRouter, createWebHistory } from "vue-router";
import tabRegistry, { getRoutes, getReservedSegments } from "./tabRegistry";
import { registerCoreTabs } from "./tabs/coreTabs";
import { registerProTabs } from "virtual:pro-tabs";

// Register core tabs
registerCoreTabs();

// Register PRO tabs from projekt_hub_pro.
// "virtual:pro-tabs" is a Vite virtual module defined in vite.config.js.
// At build time it checks if projekt_hub_pro's source exists in the bench:
//   - If yes: re-exports registerProTabs from the PRO app
//   - If no: exports a noop function (no tabs registered)
//
// On a shared bench, projekt_hub_pro's code ships to every site's bundle once
// it's deployed to the bench — so the build-time check alone isn't enough to
// gate access per customer. The actual per-site gate is whether projekt_hub_pro
// is installed on *this* site, reflected live in frappe.boot.versions (Frappe
// clears the boot info cache on install/uninstall-app, so this is accurate as
// of the last full page load — a hard refresh after installing is enough, no
// asset rebuild required).
if (typeof window !== "undefined" && window.frappe?.boot?.versions?.projekt_hub_pro) {
	registerProTabs();
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
		path: "/project-hub/:projectId/:taskId?",
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
