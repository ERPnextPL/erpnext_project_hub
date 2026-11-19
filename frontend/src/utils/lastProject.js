/**
 * Remembers where the user was in the Projects tab, so going back to that tab
 * from another one reopens the last project instead of the project list.
 *
 * Only the project view is remembered (with its filters, without an open task
 * panel); returning to the project list forgets it.
 */
const STORAGE_KEY = "projectHub.lastProjectLocation";

function storage() {
	try {
		return globalThis.window?.localStorage || null;
	} catch {
		return null;
	}
}

/** Last remembered project location: `{ path, query }`, or null. */
export function getLastProjectLocation() {
	try {
		const raw = storage()?.getItem(STORAGE_KEY);
		const value = raw ? JSON.parse(raw) : null;
		return value && typeof value.path === "string" ? value : null;
	} catch {
		return null;
	}
}

export function forgetLastProject() {
	try {
		storage()?.removeItem(STORAGE_KEY);
	} catch {
		// storage unavailable
	}
}

/** Router hook: track the Projects tab location after every navigation. */
export function rememberProjectLocation(route) {
	if (route.name === "ProjectList") {
		forgetLastProject();
		return;
	}
	if (route.name !== "ProjectOutliner" || typeof route.params.projectId !== "string") return;
	try {
		storage()?.setItem(
			STORAGE_KEY,
			JSON.stringify({
				path: `/project-hub/${encodeURIComponent(route.params.projectId)}`,
				query: { ...route.query },
			})
		);
	} catch {
		// storage unavailable - the list opens as before
	}
}
