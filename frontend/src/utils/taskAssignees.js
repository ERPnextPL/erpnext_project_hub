/**
 * Helpers for the `_assign` field of a Task (a JSON list of user ids) shared by
 * every task view: project list, project board and My Tasks.
 */

/** User ids assigned to a task. Accepts the raw `_assign` JSON or an array. */
export function parseAssignees(assign) {
	if (!assign) return [];
	if (Array.isArray(assign)) return assign.filter(Boolean);
	try {
		const parsed = JSON.parse(assign);
		return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
	} catch {
		return [];
	}
}

/** Readable name built from the user id when no full name is known. */
export function nameFromUserId(userId) {
	const local = String(userId || "").split("@")[0].replace(/[._]/g, " ").trim();
	return local ? local.charAt(0).toUpperCase() + local.slice(1) : "";
}

/** Up to two initials of a name, e.g. "Jan Kowalski" -> "JK". */
export function getInitials(name) {
	const parts = String(name || "")
		.trim()
		.split(/\s+/)
		.filter(Boolean);
	if (parts.length === 0) return "?";
	const first = parts[0].charAt(0);
	const last = parts.length > 1 ? parts[parts.length - 1].charAt(0) : "";
	return (first + last).toUpperCase();
}

/**
 * Assigned users resolved against a user list (`{ name, full_name, user_image }`,
 * as returned by the get_users API). Unknown users fall back to their id.
 */
export function resolveAssignees(assign, users = []) {
	const byId = new Map((users || []).map((user) => [user.name, user]));
	return parseAssignees(assign).map((userId) => {
		const user = byId.get(userId);
		const fullName = user?.full_name || nameFromUserId(userId);
		return {
			name: userId,
			fullName,
			image: user?.user_image || null,
			initials: getInitials(fullName),
		};
	});
}
