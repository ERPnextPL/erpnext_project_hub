import { describe, it, expect } from "vitest";
import { getInitials, nameFromUserId, parseAssignees, resolveAssignees } from "../taskAssignees";
import { getDescendants, getSubtaskStats } from "../taskHierarchy";
import { getDueState } from "../taskDueDate";

describe("taskAssignees", () => {
	it("parses the _assign JSON and ignores bad input", () => {
		expect(parseAssignees('["a@x.pl","b@x.pl"]')).toEqual(["a@x.pl", "b@x.pl"]);
		expect(parseAssignees("not json")).toEqual([]);
		expect(parseAssignees(null)).toEqual([]);
	});

	it("resolves names against the user list, falling back to the user id", () => {
		const users = [{ name: "jan@x.pl", full_name: "Jan Kowalski", user_image: "/j.png" }];
		expect(resolveAssignees('["jan@x.pl","anna.nowak@x.pl"]', users)).toEqual([
			{ name: "jan@x.pl", fullName: "Jan Kowalski", image: "/j.png", initials: "JK" },
			{ name: "anna.nowak@x.pl", fullName: "Anna nowak", image: null, initials: "AN" },
		]);
		expect(nameFromUserId("piotr_w@x.pl")).toBe("Piotr w");
		expect(getInitials("")).toBe("?");
	});
});

describe("taskHierarchy", () => {
	const tasks = [
		{ name: "A" },
		{ name: "B", parent_task: "A", status: "Completed" },
		{ name: "C", parent_task: "A", status: "Open" },
		{ name: "D", parent_task: "C", status: "Open" },
	];

	it("collects subtasks at any depth", () => {
		expect(getDescendants(tasks, "A").map((t) => t.name)).toEqual(["B", "C", "D"]);
	});

	it("counts direct subtasks and the completed ones", () => {
		expect(getSubtaskStats(tasks, "A")).toEqual({ total: 2, done: 1 });
	});
});

describe("taskDueDate", () => {
	const now = new Date(2026, 10, 12, 10, 0, 0);

	it("classifies due dates by urgency", () => {
		expect(getDueState({ exp_end_date: "2026-11-10" }, now).tone).toBe("overdue");
		expect(getDueState({ exp_end_date: "2026-11-12" }, now).tone).toBe("today");
		expect(getDueState({ exp_end_date: "2026-11-14" }, now).tone).toBe("soon");
		expect(getDueState({ exp_end_date: "2026-12-01" }, now).tone).toBe("normal");
		expect(getDueState({}, now).tone).toBe("none");
	});

	it("shows a completed task as done even past its due date", () => {
		expect(getDueState({ exp_end_date: "2026-11-01", status: "Completed" }, now).tone).toBe("done");
	});
});
