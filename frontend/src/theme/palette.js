/**
 * Light/dark colour palette of Projekt HUB.
 *
 * Every palette utility the app uses (bg, text, border, ring … with a hue and shade)
 * resolves to a CSS variable instead of a fixed hex. Light values are exactly
 * frappe-ui's light palette, so light mode renders as before. Dark values are
 * taken from frappe-ui's own dark scale (colors.json "darkMode") following the
 * mapping its semantic tokens use (surface-*, ink-*, outline-*), then nudged by
 * code until they meet WCAG contrast: text >= 4.6:1 on the lightest dark
 * surface, solid fills >= 4.6:1 against the text drawn on them.
 *
 * Each colour has three roles, because one light shade means different things
 * as a background, as text and as a border (a gray 200 background is a light surface,
 * gray 200 text a faint glyph, a gray 200 border a hairline):
 *   --hub-bg-<hue>-<shade>    backgroundColor, gradient stops, ring offset
 *   --hub-fg-<hue>-<shade>    textColor, fill, stroke, placeholder, caret, …
 *   --hub-line-<hue>-<shade>  borderColor, divideColor, ringColor, outlineColor
 *
 * The dark theme is switched on by `html.dark` (see composables/useDarkMode.js),
 * which also sets data-theme="dark" for frappe-ui's own components.
 */
import { createRequire } from "module";
import path from "path";

// frappe-ui does not export colors.json; locate it next to its Tailwind preset.
const requireFromHere = createRequire(import.meta.url);
const frappeColors = requireFromHere(
	path.join(path.dirname(requireFromHere.resolve("frappe-ui/tailwind")), "colors.json")
);

const LIGHT = frappeColors.lightMode;
const DARK = frappeColors.darkMode;
const WHITE = "#FFFFFF";
const BLACK = "#000000";

export const HUES = Object.keys(LIGHT);
// Tailwind hue names used in the app that frappe-ui's palette lacks: without
// these, classes like bg-emerald-600 generated no CSS at all (invisible badges).
export const HUE_ALIASES = { emerald: "green", slate: "gray", indigo: "violet" };
export const SHADES = ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900"];

// Contrast targets (WCAG AA is 4.5 for text, 3 for icons/borders). The margin
// covers text the app dims with opacity-75/90 (e.g. completed projects).
const TEXT_TARGET = 5.0;
const FILL_TARGET = 5.5;
// Lightest dark surface ordinary text sits on: bg-gray-200 in dark mode.
const TEXT_REFERENCE_BG = DARK.gray["600"];

// light shade -> dark shade of the same hue, per role. Gray follows frappe-ui's
// surface/ink/outline tables; colours follow their surface-<c>-n / ink-<c>-n rows.
const GRAY_MAP = {
	bg: { white: "900", 50: "700", 100: "650", 200: "600", 300: "500", 400: "400", 500: "300", 600: "250", 700: "200", 800: "100", 900: "50" },
	fg: { white: "900", 50: "800", 100: "700", 200: "600", 300: "400", 400: "400", 500: "300", 600: "250", 700: "200", 800: "100", 900: "50" },
	line: { white: "800", 50: "700", 100: "650", 200: "600", 300: "500", 400: "400", 500: "300", 600: "250", 700: "200", 800: "100", 900: "50" },
};
const HUE_MAP = {
	bg: { 50: "900", 100: "800", 200: "700", 300: "600", 400: "500", 500: "500", 600: "400", 700: "500", 800: "600", 900: "700" },
	fg: { 50: "900", 100: "900", 200: "800", 300: "400", 400: "400", 500: "400", 600: "300", 700: "200", 800: "100", 900: "50" },
	line: { 50: "900", 100: "800", 200: "800", 300: "700", 400: "600", 500: "500", 600: "400", 700: "300", 800: "200", 900: "100" },
};

// ---- colour maths ---------------------------------------------------------

export function hexToRgb(hex) {
	const value = hex.replace("#", "").slice(0, 6);
	return [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16));
}

function rgbToHex(rgb) {
	return "#" + rgb.map((c) => Math.round(c).toString(16).padStart(2, "0")).join("").toUpperCase();
}

function luminance(hex) {
	const [r, g, b] = hexToRgb(hex).map((c) => {
		const s = c / 255;
		return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
	});
	return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(a, b) {
	const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
	return (hi + 0.05) / (lo + 0.05);
}

function mix(hex, towards, amount) {
	const from = hexToRgb(hex);
	const to = hexToRgb(towards);
	return rgbToHex(from.map((c, i) => c + (to[i] - c) * amount));
}

/** Move `hex` towards white or black in 1% steps until it reaches `target` against `against`. */
function ensureContrast(hex, against, target) {
	if (contrast(hex, against) >= target) return hex;
	const towards = luminance(against) < 0.18 ? WHITE : BLACK;
	for (let step = 1; step <= 100; step += 1) {
		const candidate = mix(hex, towards, step / 100);
		if (contrast(candidate, against) >= target) return candidate;
	}
	return towards;
}

// ---- dark palette ---------------------------------------------------------

function darkValue(hue, role, shade) {
	const map = hue === "gray" ? GRAY_MAP[role] : HUE_MAP[role];
	return DARK[hue][map[shade]];
}

const DARK_TEXT_ON_FILLS = DARK.gray["900"]; // text-white & friends in dark mode

function buildDark() {
	const dark = { bg: {}, fg: {}, line: {} };
	for (const hue of HUES) {
		dark.bg[hue] = {};
		dark.fg[hue] = {};
		dark.line[hue] = {};
		for (const shade of SHADES) {
			const n = Number(shade);
			let bg = darkValue(hue, "bg", shade);
			let fg = darkValue(hue, "fg", shade);
			const line = darkValue(hue, "line", shade);

			// Solid fills (500+) carry text-white, which turns dark in dark mode.
			if (n >= 500) bg = ensureContrast(bg, DARK_TEXT_ON_FILLS, FILL_TARGET);
			// Text meant for light surfaces (300+) must read on every dark surface;
			// text meant for solid fills (50-200) must read on those fills.
			if (n >= 300) fg = ensureContrast(fg, TEXT_REFERENCE_BG, TEXT_TARGET);
			else fg = ensureContrast(fg, DARK.gray["200"], TEXT_TARGET);

			dark.bg[hue][shade] = bg;
			dark.fg[hue][shade] = fg;
			dark.line[hue][shade] = line;
		}
	}
	dark.bg.white = DARK.gray["900"];
	dark.fg.white = DARK_TEXT_ON_FILLS;
	dark.line.white = DARK.gray["800"];
	// Black stays black as a backdrop/scrim; black text turns light.
	dark.bg.black = BLACK;
	dark.fg.black = DARK.gray["50"];
	dark.line.black = DARK.gray["50"];
	return dark;
}

function buildLight() {
	const light = { bg: {}, fg: {}, line: {} };
	for (const role of Object.keys(light)) {
		for (const hue of HUES) {
			light[role][hue] = {};
			for (const shade of SHADES) light[role][hue][shade] = LIGHT[hue][shade];
		}
		light[role].white = WHITE;
		light[role].black = BLACK;
	}
	return light;
}

export const lightPalette = buildLight();
export const darkPalette = buildDark();

// ---- Tailwind glue --------------------------------------------------------

const varName = (role, hue, shade) => (shade ? `--hub-${role}-${hue}-${shade}` : `--hub-${role}-${hue}`);
const rgbChannels = (hex) => hexToRgb(hex).join(" ");

/** Tailwind colour map of one role: { gray: { 50: "rgb(var(--hub-bg-gray-50) / <alpha-value>)" }, white: … } */
export function tailwindColors(role) {
	const colors = {};
	for (const hue of HUES) {
		colors[hue] = {};
		for (const shade of SHADES) {
			colors[hue][shade] = `rgb(var(${varName(role, hue, shade)}) / <alpha-value>)`;
		}
	}
	for (const [alias, hue] of Object.entries(HUE_ALIASES)) colors[alias] = colors[hue];
	colors.white = `rgb(var(${varName(role, "white")}) / <alpha-value>)`;
	colors.black = `rgb(var(${varName(role, "black")}) / <alpha-value>)`;
	return colors;
}

function declarations(palette) {
	const out = {};
	for (const role of ["bg", "fg", "line"]) {
		for (const hue of HUES) {
			for (const shade of SHADES) out[varName(role, hue, shade)] = rgbChannels(palette[role][hue][shade]);
		}
		out[varName(role, "white")] = rgbChannels(palette[role].white);
		out[varName(role, "black")] = rgbChannels(palette[role].black);
	}
	return out;
}

/** Base styles declaring the variables: light on :root, dark on html.dark. */
export function paletteBaseStyles() {
	return {
		":root": declarations(lightPalette),
		":root.dark": declarations(darkPalette),
	};
}

/**
 * On the live page Frappe's website CSS (Bootstrap 4) loads first, and its
 * utilities share names with Tailwind's while carrying !important:
 * .bg-white, .text-white and .border-white (`.border` is handled by
 * scripts/theme-border-guard.js).
 * They pin those colours to white in dark mode, so in dark mode these rules
 * win back with a more specific selector. Light mode is left as it was.
 */
export function bootstrapDarkGuards() {
	const rules = {
		"html.dark .bg-white": {
			"background-color": "rgb(var(--hub-bg-white) / var(--tw-bg-opacity, 1)) !important",
		},
		"html.dark .text-white": {
			color: "rgb(var(--hub-fg-white) / var(--tw-text-opacity, 1)) !important",
		},
		"html.dark .border-white": {
			"border-color": "rgb(var(--hub-line-white) / var(--tw-border-opacity, 1)) !important",
		},
	};
	return rules;
}
