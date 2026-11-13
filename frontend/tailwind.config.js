import plugin from "tailwindcss/plugin";
import { tailwindColors, paletteBaseStyles } from "./src/theme/palette.js";

// Palette utilities resolve to CSS variables that switch with the dark theme;
// see src/theme/palette.js for the roles (bg / fg / line) and how dark values
// are derived.
const bg = tailwindColors("bg");
const fg = tailwindColors("fg");
const line = tailwindColors("line");

/** @type {import('tailwindcss').Config} */
export default {
	presets: [require("frappe-ui/tailwind")],
	darkMode: "class",
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		"../node_modules/frappe-ui/src/**/*.{vue,js,ts}",
	],
	// Accent classes of tabs registered by plugins (tab.color / tab.bg), which
	// OutlinerNav renders but this build never sees in its sources.
	safelist: [{ pattern: /^(text-[a-z]+-600|bg-[a-z]+-50)$/ }],
	theme: {
		extend: {
			colors: {
				...fg,
				"task-open": "#3b82f6",
				"task-working": "#f59e0b",
				"task-completed": "#10b981",
				"task-overdue": "#ef4444",
				"task-cancelled": "#6b7280",
			},
			backgroundColor: bg,
			gradientColorStops: bg,
			ringOffsetColor: bg,
			borderColor: line,
			divideColor: line,
			// Tailwind's default ring (blue-500 at 50%) must follow the palette too.
			ringColor: {
				...line,
				DEFAULT: ({ opacityValue = "1" }) => `rgb(var(--hub-line-blue-500) / ${opacityValue})`,
			},
			outlineColor: line,
		},
	},
	plugins: [
		plugin(({ addBase }) => {
			addBase(paletteBaseStyles());
		}),
	],
};
