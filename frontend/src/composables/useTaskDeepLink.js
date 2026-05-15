import { computed, ref, watch } from "vue";

function normalizeTaskQuery(value) {
	if (Array.isArray(value)) {
		value = value[0];
	}

	return typeof value === "string" ? value.trim() : "";
}

function buildRouteLocation(route, taskName, options) {
	const { mode = "query", paramName = "taskId", queryName = "task" } = options || {};
	const query = { ...(route.query || {}) };
	const location = {
	};

	if (route.name) {
		location.name = route.name;
		location.params = { ...(route.params || {}) };
	} else {
		location.path = route.path;
	}

	if (mode === "param") {
		if (taskName) {
			location.params[paramName] = taskName;
		} else {
			delete location.params[paramName];
		}
	} else {
		if (taskName) {
			query[queryName] = taskName;
		} else {
			delete query[queryName];
		}
		location.query = query;
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
	mode = "query",
	paramName = "taskId",
	queryName = "task",
}) {
	const syncingFromRoute = ref(false);
	let routeRequestId = 0;
	const taskNameFromRoute = computed(() =>
		mode === "param"
			? normalizeTaskQuery(route.params?.[paramName])
			: normalizeTaskQuery(route.query?.[queryName])
	);

	async function syncRoute(taskName, replace = false) {
		const normalizedTaskName = normalizeTaskQuery(taskName);
		const nextLocation = buildRouteLocation(route, normalizedTaskName, {
			mode,
			paramName,
			queryName,
		});

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
