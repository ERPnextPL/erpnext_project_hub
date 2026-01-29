import { ref, watch, onMounted } from 'vue';

const isDark = ref(false);
const THEME_KEY = 'project-hub-theme';

export function useDarkMode() {
	// Initialize theme
	function initTheme() {
		// Force light theme and clear stored preference
		localStorage.removeItem(THEME_KEY);
		isDark.value = false;
		applyTheme();
	}

	// Apply theme to document
	function applyTheme() {
		// Dark mode disabled: always ensure light classes
		document.documentElement.classList.remove('dark');
	}

	// Toggle theme
	function toggleTheme() {
		// No-op, keep light theme
		isDark.value = false;
		localStorage.removeItem(THEME_KEY);
		applyTheme();
	}

	// Set specific theme
	function setTheme(theme) {
		isDark.value = false;
		localStorage.removeItem(THEME_KEY);
		applyTheme();
	}

	// Listen for system theme changes
	function listenToSystemTheme() {
		// Dark mode disabled; no listeners required
		return () => {};
	}

	return {
		isDark,
		toggleTheme,
		setTheme,
		initTheme,
		listenToSystemTheme,
	};
}
