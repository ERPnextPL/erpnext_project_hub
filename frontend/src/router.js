import { createRouter, createWebHistory } from "vue-router";
import tabRegistry, { getRoutes, getReservedSegments } from "./tabRegistry";

/**
 * Build the router from the tab registry. Call it only once every tab is
 * registered (core tabs and plugins, see main.js): routes and reserved URL
 * segments are read from the registry here.
 */
export function createAppRouter() {
	tabRegistry.markInitialized();

	const reservedProjectSegments = getReservedSegments();

	const routes = [
		// Add all registered tab routes
		...getRoutes(),
		// Project Outliner route (must come last to avoid conflicts)
		{
			path: "/project-hub/:projectId/:taskId?",
			name: "ProjectOutliner",
			component: () => import("./pages/ProjectOutliner.vue"),
			props: true,
			beforeEnter(to) {
				const segment = to.params.projectId;
				if (typeof segment !== "string") return;
				if (reservedProjectSegments[segment]) {
					return { name: reservedProjectSegments[segment] };
				}
			},
		},
	];

	return createRouter({
		history: createWebHistory(),
		routes,
	});
}
