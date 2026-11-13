import { describe, it, expect, beforeEach } from "vitest";

// Minimal browser stand-ins (the frontend tests run without a DOM environment).
globalThis.window = globalThis.window || { frappe: null, __: (text) => text };
globalThis.document = globalThis.document || { createElement: () => ({ style: {}, setAttribute() {} }) };

const { createPinia, setActivePinia } = await import("pinia");
const { useTaskStore } = await import("../taskStore");

const PROJECT = "PROJ-1";
const task = (name, status, extra = {}) => ({ name, subject: name, status, project: PROJECT, _assign: "[]", ...extra });

// Fake backend: project tasks by status, task updates echo the new fields.
function installBackend(db) {
	const calls = [];
	globalThis.fetch = async (url, init) => {
		const method = String(url).split("/api/method/")[1];
		const params = Object.fromEntries(init?.body?.entries?.() || []);
		calls.push({ method, params });
		let message = null;
		if (method.endsWith("get_project_tasks")) {
			const statuses = params.status ? params.status.split(",") : ["Open", "Working"];
			message = { tasks: db.filter((t) => statuses.includes(t.status)), project: { name: PROJECT, completed_tasks: db.filter((t) => t.status === "Completed").length } };
		} else if (method.endsWith("update_task")) {
			const row = db.find((t) => t.name === params.task_name);
			Object.assign(row, params.status ? { status: params.status } : {});
			message = { ...row };
		} else if (method.endsWith("assign_task")) {
			message = { _assign: JSON.stringify([params.user]) };
		} else if (method.endsWith("delete_task")) {
			db.splice(db.findIndex((t) => t.name === params.task_name), 1);
			message = { ok: true };
		} else {
			message = [];
		}
		// Serialise like a real response: no object is shared with the "database".
		const body = JSON.stringify({ message });
		return { ok: true, json: async () => JSON.parse(body) };
	};
	return calls;
}

describe("taskStore: board tasks loaded on demand (Completed list)", () => {
	let db;
	let store;
	beforeEach(async () => {
		setActivePinia(createPinia());
		db = [task("OPEN-1", "Open"), task("DONE-1", "Completed"), task("DONE-2", "Completed")];
		installBackend(db);
		store = useTaskStore();
		await store.fetchTasks(PROJECT);
		await store.fetchCompletedProjectTasks(PROJECT);
	});

	it("keeps loaded completed tasks in the shared store, apart from the list", () => {
		expect(store.tasks.map((t) => t.name)).toEqual(["OPEN-1"]);
		expect(store.boardExtraTasks.map((t) => t.name)).toEqual(["DONE-1", "DONE-2"]);
	});

	it("moving a loaded card from Completed to Open updates the stored record", async () => {
		const result = await store.updateTask("DONE-1", { status: "Open" });
		expect(result.status).toBe("Open");
		expect(store.boardExtraTasks.find((t) => t.name === "DONE-1").status).toBe("Open");
		// The list itself is not widened by the board's extras.
		expect(store.tasks.map((t) => t.name)).toEqual(["OPEN-1"]);
	});

	it("assignment and deletion reach loaded tasks too", async () => {
		await store.assignTask("DONE-2", "anna@example.com", "add");
		expect(store.boardExtraTasks.find((t) => t.name === "DONE-2")._assign).toContain("anna@example.com");
		await store.deleteTask("DONE-2");
		expect(store.boardExtraTasks.some((t) => t.name === "DONE-2")).toBe(false);
	});

	it("a refetch that now lists a loaded task drops the duplicate extra", async () => {
		await store.updateTask("DONE-1", { status: "Open" });
		await store.fetchTasks(PROJECT);
		expect(store.tasks.map((t) => t.name).sort()).toEqual(["DONE-1", "OPEN-1"]);
		expect(store.boardExtraTasks.map((t) => t.name)).toEqual(["DONE-2"]);
	});

	it("another project's extras are dropped", async () => {
		await store.fetchTasks("PROJ-2");
		expect(store.boardExtraTasks).toEqual([]);
	});
});
