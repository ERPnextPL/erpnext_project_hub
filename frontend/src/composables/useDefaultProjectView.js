import { ref } from "vue";

export const PROJECT_VIEWS = ["list", "board", "timeline"];
const STORAGE_KEY = "project-hub-default-project-view";
const FALLBACK_VIEW = "list";

function readStoredView() {
	try {
		const stored = window.localStorage.getItem(STORAGE_KEY);
		return PROJECT_VIEWS.includes(stored) ? stored : FALLBACK_VIEW;
	} catch {
		return FALLBACK_VIEW;
	}
}

// Shared across components so every page sees the same preference.
const defaultProjectView = ref(readStoredView());

export function useDefaultProjectView() {
	function setDefaultProjectView(view) {
		if (!PROJECT_VIEWS.includes(view)) return;
		defaultProjectView.value = view;
		try {
			window.localStorage.setItem(STORAGE_KEY, view);
		} catch {
			// Storage unavailable (private mode etc.) — keep the in-memory value.
		}
	}

	return { defaultProjectView, setDefaultProjectView };
}
