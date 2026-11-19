import { describe, it, expect } from "vitest";
import { applyMoveToLoaded, cardsForStatus } from "../boardLoadedTasks";

const t = (name, status) => ({ name, status });

describe("board-loaded cards", () => {
	it("a loaded card moved from Completed to Open shows under Open after the save", () => {
		const loaded = new Map([["Completed", [t("DONE-1", "Completed"), t("DONE-2", "Completed")]]]);
		applyMoveToLoaded(loaded, "DONE-1", "Open", { name: "DONE-1", status: "Open", priority: "High" });
		expect(cardsForStatus([t("OPEN-1", "Open")], loaded, "Open").map((c) => c.name)).toEqual(["OPEN-1", "DONE-1"]);
		expect(cardsForStatus([], loaded, "Completed").map((c) => c.name)).toEqual(["DONE-2"]);
		expect(loaded.get("Completed")[0].priority).toBe("High");
	});

	it("a failed or cancelled move leaves the card where it was", () => {
		const loaded = new Map([["Completed", [t("DONE-1", "Completed")]]]);
		applyMoveToLoaded(loaded, "DONE-1", "Open", null);
		expect(cardsForStatus([], loaded, "Completed").map((c) => c.name)).toEqual(["DONE-1"]);
		expect(cardsForStatus([], loaded, "Open")).toEqual([]);
	});

	it("the owner's fresher copy wins over a stale loaded one (no card in two lists)", () => {
		const loaded = new Map([["Completed", [t("DONE-1", "Completed")]]]);
		const owner = [t("DONE-1", "Working")];
		expect(cardsForStatus(owner, loaded, "Working").map((c) => c.name)).toEqual(["DONE-1"]);
		expect(cardsForStatus(owner, loaded, "Completed")).toEqual([]);
	});

	it("uses the board's own status mapping", () => {
		const loaded = new Map();
		const owner = [t("OLD-1", "Overdue")];
		const statusOf = (task) => (task.status === "Overdue" ? "Open" : task.status);
		expect(cardsForStatus(owner, loaded, "Open", statusOf).map((c) => c.name)).toEqual(["OLD-1"]);
	});
});
