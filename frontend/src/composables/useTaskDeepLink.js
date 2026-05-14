import { computed, ref, watch } from "vue";

function normalizeTaskQuery(value) {
	if (Array.isArray(value)) {
		value = value[0];
	}

	return typeof value === "string" ? value.trim() : "";
}

function buildRouteLocation(route, taskName) {
	const query = { ...(route.query || {}) };

	if (taskName) {
		query.task = taskName;
	} else {
		delete query.task;
	}

	const location = {
		query,
	};

	if (route.name) {
		location.name = route.name;
		location.params = route.params;
	} else {
		location.path = route.path;
	}

	if (route.hash) {
		location.hash = route.hash;
	}

	return location;
}

export function useTaskDeepLink({
	route,
	router,
	selectedTask,
	selectTask,
	clearSelection,
	resolveTask,
	loadTaskDetail,
}) {
	const syncingFromRoute = ref(false);
	let routeRequestId = 0;
	const taskNameFromRoute = computed(() => normalizeTaskQuery(route.query?.task));

	async function syncRoute(taskName, replace = false) {
		const normalizedTaskName = normalizeTaskQuery(taskName);
		const nextLocation = buildRouteLocation(route, normalizedTaskName);

		if (normalizedTaskName === taskNameFromRoute.value) {
			return;
		}

		if (replace) {
			await router.replace(nextLocation);
			return;
		}

		await router.push(nextLocation);
	}

	async function openTaskFromRoute(taskName) {
		const requestId = ++routeRequestId;
		syncingFromRoute.value = true;

		try {
			if (!taskName) {
				if (selectedTask.value) {
					clearSelection();
				}
				return;
			}

			const existingTask = resolveTask?.(taskName) || null;
			if (existingTask && requestId === routeRequestId && taskName === taskNameFromRoute.value) {
				selectTask(existingTask);
				return;
			}

			if (loadTaskDetail) {
				try {
					const taskDetail = await loadTaskDetail(taskName);
					if (requestId !== routeRequestId || taskName !== taskNameFromRoute.value) {
						return;
					}

					if (taskDetail) {
						selectTask(taskDetail);
						return;
					}
				} catch (error) {
					console.error("Failed to load task from route:", error);
				}
			}

			if (requestId !== routeRequestId || taskName !== taskNameFromRoute.value) {
				return;
			}

			if (selectedTask.value) {
				clearSelection();
			}
			await syncRoute("", true);
		} finally {
			if (requestId === routeRequestId) {
				syncingFromRoute.value = false;
			}
		}
	}

	watch(
		taskNameFromRoute,
		(taskName) => {
			void openTaskFromRoute(taskName);
		},
		{ immediate: true }
	);

	watch(
		() => selectedTask.value?.name || "",
		(taskName) => {
			if (syncingFromRoute.value) {
				return;
			}

			if (!taskName) {
				if (taskNameFromRoute.value) {
					void syncRoute("", true);
				}
				return;
			}

			void syncRoute(taskName, false);
		}
	);
}
