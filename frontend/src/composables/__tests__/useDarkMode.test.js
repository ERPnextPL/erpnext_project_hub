import { describe, it, expect, beforeEach } from "vitest";

// Minimal browser stand-ins (the frontend tests run without a DOM environment).
const listeners = {};
const store = new Map();
const classes = new Set();
const attributes = new Map();
globalThis.localStorage = {
	getItem: (key) => (store.has(key) ? store.get(key) : null),
	setItem: (key, value) => store.set(key, String(value)),
	clear: () => store.clear(),
};
globalThis.window = {
	localStorage: globalThis.localStorage,
	addEventListener: (type, fn) => (listeners[type] ||= []).push(fn),
	dispatchEvent: (event) => (listeners[event.type] || []).forEach((fn) => fn(event)),
};
globalThis.document = {
	createElement: () => ({ style: {}, setAttribute() {} }),
	documentElement: {
		classList: {
			contains: (name) => classes.has(name),
			toggle: (name, force) => (force ? classes.add(name) : classes.delete(name)),
		},
		getAttribute: (name) => (attributes.has(name) ? attributes.get(name) : null),
		setAttribute: (name, value) => attributes.set(name, value),
		removeAttribute: (name) => attributes.delete(name),
	},
};
const storageEvent = (key, newValue) => ({ type: "storage", key, newValue });

const { useDarkMode, THEME_KEY } = await import("../useDarkMode");
const root = () => document.documentElement;

describe("useDarkMode", () => {
	beforeEach(() => {
		localStorage.clear();
		classes.clear();
		root().removeAttribute("data-theme");
	});

	it("defaults to light when nothing is stored", () => {
		const { isDark, initTheme } = useDarkMode();
		initTheme();
		expect(isDark.value).toBe(false);
		expect(root().classList.contains("dark")).toBe(false);
		expect(root().getAttribute("data-theme")).toBe("light");
	});

	it("restores a stored dark theme", () => {
		localStorage.setItem(THEME_KEY, "dark");
		const { isDark, initTheme } = useDarkMode();
		initTheme();
		expect(isDark.value).toBe(true);
		expect(root().classList.contains("dark")).toBe(true);
		expect(root().getAttribute("data-theme")).toBe("dark");
	});

	it("toggles and persists the choice", () => {
		const { isDark, initTheme, toggleTheme } = useDarkMode();
		initTheme();
		toggleTheme();
		expect(isDark.value).toBe(true);
		expect(localStorage.getItem(THEME_KEY)).toBe("dark");
		expect(root().classList.contains("dark")).toBe(true);
		toggleTheme();
		expect(isDark.value).toBe(false);
		expect(localStorage.getItem(THEME_KEY)).toBe("light");
		expect(root().classList.contains("dark")).toBe(false);
	});

	it("ignores unknown stored values", () => {
		localStorage.setItem(THEME_KEY, "unknown-theme");
		const { isDark, initTheme } = useDarkMode();
		initTheme();
		expect(isDark.value).toBe(false);
	});

	it("follows a change made in another window", () => {
		const { isDark, initTheme } = useDarkMode();
		initTheme();
		window.dispatchEvent(storageEvent(THEME_KEY, "dark"));
		expect(isDark.value).toBe(true);
		expect(root().classList.contains("dark")).toBe(true);
	});
});
