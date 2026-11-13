import { describe, it, expect } from "vitest";
import postcss from "postcss";
import themeBorderGuard from "../theme-border-guard.js";

const run = async (css) => (await postcss([themeBorderGuard]).process(css, { from: undefined })).css;

describe("theme-border-guard", () => {
	it("adds !important twins scoped to .border for border utilities", async () => {
		const out = await run(".border-blue-500{--tw-border-opacity:1;border-color:rgb(0 0 255)}");
		expect(out).toContain(".border.border-blue-500");
		expect(out).toMatch(/\.border\.border-blue-500\s*\{[^}]*border-color:\s*rgb\(0 0 255\)\s*!important/);
	});

	it("handles escaped variant selectors and media queries", async () => {
		const out = await run(
			".hover\\:border-red-400:hover{border-color:red}@media (min-width:640px){.sm\\:border-dashed{border-style:dashed}}"
		);
		expect(out).toContain(".border.hover\\:border-red-400:hover");
		expect(out).toMatch(/@media \(min-width:640px\)\s*\{\s*\.border\.sm\\:border-dashed/);
	});

	it("puts the guard on the last compound of group selectors", async () => {
		const out = await run(".group:hover .group-hover\\:border-blue-200{border-color:blue}");
		expect(out).toContain(".group:hover .border.group-hover\\:border-blue-200");
	});

	it("leaves non-border rules and .border itself alone", async () => {
		const out = await run(".border{border-width:1px}.border-separate{border-collapse:separate}.text-red-500{color:red}");
		expect(out).not.toContain(".border.border-separate");
		expect(out).not.toContain(".border.text-red-500");
		expect(out).not.toMatch(/\.border\.border\{border-width/);
	});
});
