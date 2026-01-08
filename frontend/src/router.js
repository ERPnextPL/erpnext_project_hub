import { createRouter, createWebHistory } from "vue-router";

const RESERVED_PROJECT_SEGMENTS = {
	"my-tasks": "MyTasks",
	"my-time-logs": "MyTimeLogs",
	"team-manager": "TeamManager",
	"time-management": "TimeManagement",
};

const routes = [
	{
		path: "/project-hub",
		name: "ProjectList",
		component: () => import("./pages/ProjectList.vue"),
	},
	{
		path: "/project-hub/my-tasks",
		name: "MyTasks",
		component: () => import("./pages/MyTasks.vue"),
	},
	{
		path: "/project-hub/my-time-logs",
		name: "MyTimeLogs",
		component: () => import("./pages/MyTimeLogs.vue"),
	},
	{
		path: "/project-hub/team-manager",
		name: "TeamManager",
		component: () => import("./pages/TeamManager.vue"),
	},
	{
		path: "/project-hub/time-management",
		name: "TimeManagement",
		component: () => import("./pages/TimeManagement.vue"),
	},
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
