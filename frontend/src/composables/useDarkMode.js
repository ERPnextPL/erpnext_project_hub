import { ref } from "vue";

/**
 * Light / dark theme of Projekt HUB.
 *
 * The choice is stored per browser under THEME_KEY ("light" | "dark"; light when
 * nothing is stored). Dark mode sets `class="dark"` on <html>, which switches the
 * palette variables (src/theme/palette.js), and `data-theme="dark"`, which
 * switches frappe-ui's own components. project-hub.html / index.html apply the
 * stored theme before the app mounts so pages never flash light.
 */
export const THEME_KEY = "project-hub-theme";
export const THEMES = ["light", "dark"];

const isDark = ref(false);
let storageListenerInstalled = false;

function readStoredTheme() {
	try {
		const stored = window.localStorage.getItem(THEME_KEY);
		return THEMES.includes(stored) ? stored : null;
	} catch {
		return null;
	}
}

function writeStoredTheme(theme) {
	try {
		window.localStorage.setItem(THEME_KEY, theme);
	} catch {
		// Private mode / blocked storage: the theme still applies to this page.
	}
}

export function applyTheme(theme) {
	const dark = theme === "dark";
	const root = document.documentElement;
	root.classList.toggle("dark", dark);
	root.setAttribute("data-theme", dark ? "dark" : "light");
	isDark.value = dark;
}

// Other windows of the app (e.g. the requests board opened in its own window)
// follow a change made in this one.
function onStorage(event) {
	if (event.key !== THEME_KEY) return;
	applyTheme(THEMES.includes(event.newValue) ? event.newValue : "light");
}

export function useDarkMode() {
	function initTheme() {
		applyTheme(readStoredTheme() || "light");
		if (!storageListenerInstalled && typeof window !== "undefined") {
			window.addEventListener("storage", onStorage);
			storageListenerInstalled = true;
		}
	}

	function setTheme(theme) {
		const next = THEMES.includes(theme) ? theme : "light";
		writeStoredTheme(next);
		applyTheme(next);
	}

	function toggleTheme() {
		setTheme(isDark.value ? "light" : "dark");
	}

	return { isDark, initTheme, setTheme, toggleTheme };
}
