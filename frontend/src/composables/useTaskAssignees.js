import { computed } from "vue";
import { useTaskStore } from "../stores/taskStore";

/**
 * Composable for handling task assignee display logic.
 * Provides computed properties for user maps and first assignee info.
 */
export function useTaskAssignees(taskProp) {
	const store = useTaskStore();

	const assignedUsers = computed(() => {
		if (!taskProp.value._assign) return [];
		try {
			const assigns = JSON.parse(taskProp.value._assign);
			return Array.isArray(assigns) ? assigns : [];
		} catch {
			return [];
		}
	});

	const usersByEmail = computed(() => {
		return new Map((store.availableUsers || []).map((u) => [u.name, u]));
	});

	const firstAssignee = computed(() => {
		if (assignedUsers.value.length === 0) return null;
		const email = assignedUsers.value[0];
		const user = usersByEmail.value.get(email);
		const displayName = user?.full_name || user?.name || email;
		const initials = displayName.trim().charAt(0).toUpperCase() || "?";
		return {
			email,
			displayName,
			initials,
		};
	});

	return {
		assignedUsers,
		usersByEmail,
		firstAssignee,
	};
}
