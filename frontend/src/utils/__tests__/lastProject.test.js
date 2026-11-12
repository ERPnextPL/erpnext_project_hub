import { describe, it, expect, beforeEach } from "vitest";
import { forgetLastProject, getLastProjectLocation, rememberProjectLocation } from "../lastProject";

const store = new Map();
globalThis.window = {
	localStorage: {
		getItem: (key) => (store.has(key) ? store.get(key) : null),
		setItem: (key, value) => store.set(key, String(value)),
		removeItem: (key) => store.delete(key),
	},
};

describe("lastProject", () => {
	beforeEach(() => forgetLastProject());

	it("remembers the opened project with its filters but without the task panel", () => {
		rememberProjectLocation({
			name: "ProjectOutliner",
			params: { projectId: "PROJ-0001", taskId: "TASK-1" },
			query: { status: "Open" },
		});
		expect(getLastProjectLocation()).toEqual({
			path: "/project-hub/PROJ-0001",
			query: { status: "Open" },
		});
	});

	it("forgets it when the user goes back to the project list", () => {
		rememberProjectLocation({ name: "ProjectOutliner", params: { projectId: "P" }, query: {} });
		rememberProjectLocation({ name: "ProjectList", params: {}, query: {} });
		expect(getLastProjectLocation()).toBeNull();
	});

	it("keeps it while the user is on other tabs", () => {
		rememberProjectLocation({ name: "ProjectOutliner", params: { projectId: "P" }, query: {} });
		rememberProjectLocation({ name: "MyTasks", params: {}, query: {} });
		expect(getLastProjectLocation()?.path).toBe("/project-hub/P");
	});
});
