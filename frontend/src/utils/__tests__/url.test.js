import { describe, it, expect } from "vitest";
import { toOpenableUrl } from "../url";

describe("toOpenableUrl", () => {
	it("returns empty string for empty values", () => {
		expect(toOpenableUrl("")).toBe("");
		expect(toOpenableUrl("   ")).toBe("");
		expect(toOpenableUrl(null)).toBe("");
		expect(toOpenableUrl(undefined)).toBe("");
	});

	it("keeps http and https URLs", () => {
		expect(toOpenableUrl("https://docs.example.com/a")).toBe("https://docs.example.com/a");
		expect(toOpenableUrl(" http://example.com ")).toBe("http://example.com");
	});

	it("adds https when no scheme is given", () => {
		expect(toOpenableUrl("github.com/org/repo")).toBe("https://github.com/org/repo");
	});

	it("rejects non-http schemes", () => {
		expect(toOpenableUrl("javascript:alert(1)")).toBe("");
		expect(toOpenableUrl("data:text/html,x")).toBe("");
		expect(toOpenableUrl("ftp://example.com")).toBe("");
	});
});
