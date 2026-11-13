import { describe, it, expect } from "vitest";
import { HUE_ALIASES, HUES, SHADES, contrast, darkPalette, lightPalette, tailwindColors, paletteBaseStyles } from "../palette";

const DARK_SURFACES = ["white", ...["50", "100", "200"].map((s) => `gray-${s}`)];
const surface = (key) => (key === "white" ? darkPalette.bg.white : darkPalette.bg.gray[key.split("-")[1]]);

describe("palette", () => {
	it("keeps light values identical to frappe-ui's light palette", () => {
		expect(lightPalette.bg.gray["50"]).toBe("#F8F8F8");
		expect(lightPalette.fg.blue["600"]).toBe("#007BE0");
		expect(lightPalette.line.red["200"]).toBe("#FFD8D8");
		expect(lightPalette.bg.white).toBe("#FFFFFF");
	});

	it("dark text shades 300-900 of every hue read >= 4.5:1 on every dark gray surface", () => {
		for (const hue of HUES) {
			for (const shade of SHADES.filter((s) => Number(s) >= 300)) {
				for (const key of DARK_SURFACES) {
					const ratio = contrast(darkPalette.fg[hue][shade], surface(key));
					expect(ratio, `text-${hue}-${shade} on bg-${key}`).toBeGreaterThanOrEqual(4.5);
				}
			}
		}
	});

	it("dark solid fills (500-900) keep text-white readable", () => {
		for (const hue of HUES) {
			for (const shade of ["500", "600", "700", "800", "900"]) {
				const ratio = contrast(darkPalette.bg[hue][shade], darkPalette.fg.white);
				expect(ratio, `text-white on bg-${hue}-${shade}`).toBeGreaterThanOrEqual(4.5);
			}
		}
	});

	it("dark surfaces are dark", () => {
		expect(contrast(darkPalette.bg.white, "#000000")).toBeLessThan(1.5);
		expect(contrast(darkPalette.bg.gray["50"], "#000000")).toBeLessThan(1.5);
	});

	it("maps Tailwind hue names missing from frappe-ui onto existing hues", () => {
		const colors = tailwindColors("fg");
		for (const [alias, hue] of Object.entries(HUE_ALIASES)) expect(colors[alias]).toEqual(colors[hue]);
	});

	it("exposes every hue/shade as a CSS variable for light and dark", () => {
		const styles = paletteBaseStyles();
		const colors = tailwindColors("bg");
		expect(colors.gray["200"]).toBe("rgb(var(--hub-bg-gray-200) / <alpha-value>)");
		for (const selector of [":root", ":root.dark"]) {
			for (const role of ["bg", "fg", "line"]) {
				for (const hue of HUES) {
					for (const shade of SHADES) {
						expect(styles[selector][`--hub-${role}-${hue}-${shade}`]).toMatch(/^\d+ \d+ \d+$/);
					}
				}
			}
		}
	});
});
