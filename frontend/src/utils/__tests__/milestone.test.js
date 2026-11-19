import { describe, it, expect } from "vitest";
import { DEFAULT_MILESTONE_COLOR, getTaskMilestone } from "../milestone";

describe("getTaskMilestone", () => {
	it("returns null for a task without a milestone", () => {
		expect(getTaskMilestone({ name: "T" })).toBeNull();
	});

	it("takes name and colour from the project milestones", () => {
		const milestones = [{ name: "M-1", milestone_name: "MVP", color: "#8b5cf6" }];
		expect(getTaskMilestone({ milestone: "M-1" }, milestones)).toEqual({
			name: "M-1",
			label: "MVP",
			color: "#8b5cf6",
		});
	});

	it("falls back to the fields sent with the task, then to defaults", () => {
		expect(
			getTaskMilestone({ milestone: "M-2", milestone_name: "Go-live", milestone_color: "#0ea5e9" })
		).toEqual({ name: "M-2", label: "Go-live", color: "#0ea5e9" });
		expect(getTaskMilestone({ milestone: "M-3" })).toEqual({
			name: "M-3",
			label: "M-3",
			color: DEFAULT_MILESTONE_COLOR,
		});
	});
});
