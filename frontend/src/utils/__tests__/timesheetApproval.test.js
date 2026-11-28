import { describe, it, expect } from "vitest";
import {
	APPROVAL,
	getApprovalBadge,
	getApprovalState,
	isEditableLog,
	rejectedTimesheets,
	summarizeApproval,
	timesheetsToSend,
} from "../timesheetApproval";

const draft = { timesheet_name: "TS-1", docstatus: 0, workflow_state: "Draft", hours: 2 };
const draftSameSheet = { timesheet_name: "TS-1", docstatus: 0, workflow_state: "Draft", hours: 1.5 };
const pending = { timesheet_name: "TS-2", docstatus: 0, workflow_state: "Pending Approval", hours: 3 };
const rejected = {
	timesheet_name: "TS-3",
	docstatus: 0,
	workflow_state: "Rejected",
	hours: 4,
	rejection_reason: "Wrong project",
	reviewed_by: "boss@example.com",
	reviewed_by_name: "Boss",
};
const approved = { timesheet_name: "TS-4", docstatus: 1, workflow_state: "Approved", status: "Submitted", hours: 5 };
const billed = { timesheet_name: "TS-5", docstatus: 1, workflow_state: "Approved", status: "Billed", hours: 6 };

describe("getApprovalState", () => {
	it("reads the workflow state", () => {
		expect(getApprovalState(pending)).toBe(APPROVAL.PENDING);
	});

	it("falls back to the docstatus for timesheets without a state", () => {
		expect(getApprovalState({ docstatus: 0 })).toBe(APPROVAL.DRAFT);
		expect(getApprovalState({ docstatus: 1 })).toBe(APPROVAL.APPROVED);
		expect(getApprovalState({ docstatus: 2 })).toBe(APPROVAL.CANCELLED);
	});
});

describe("isEditableLog", () => {
	it("allows drafts and rejected entries only", () => {
		expect(isEditableLog(draft)).toBe(true);
		expect(isEditableLog(rejected)).toBe(true);
		expect(isEditableLog(pending)).toBe(false);
		expect(isEditableLog(approved)).toBe(false);
	});
});

describe("getApprovalBadge", () => {
	it("colours the approval stages", () => {
		expect(getApprovalBadge(draft)).toEqual({ label: "Draft", tone: "gray" });
		expect(getApprovalBadge(pending)).toEqual({ label: "Pending Approval", tone: "orange" });
		expect(getApprovalBadge(rejected)).toEqual({ label: "Rejected", tone: "red" });
		expect(getApprovalBadge(approved)).toEqual({ label: "Approved", tone: "green" });
	});

	it("shows the billing status of approved entries once billed", () => {
		expect(getApprovalBadge(billed)).toEqual({ label: "Billed", tone: "blue" });
	});
});

describe("summarizeApproval", () => {
	it("counts rejected entries as still to send", () => {
		const summary = summarizeApproval([draft, draftSameSheet, pending, rejected, approved, billed]);
		expect(summary.toSendHours).toBe(7.5);
		expect(summary.toSendCount).toBe(3);
		expect(summary.rejectedCount).toBe(1);
		expect(summary.pendingHours).toBe(3);
		expect(summary.approvedHours).toBe(11);
		expect(summary.approvedCount).toBe(2);
	});
});

describe("timesheetsToSend", () => {
	it("lists each draft or rejected timesheet once", () => {
		const result = timesheetsToSend([draft, draftSameSheet, pending, rejected, approved]);
		expect(result.timesheets).toEqual(["TS-1", "TS-3"]);
		expect(result.hours).toBe(7.5);
	});
});

describe("rejectedTimesheets", () => {
	it("groups rejected entries by timesheet with the reason", () => {
		const second = { ...rejected, hours: 1 };
		expect(rejectedTimesheets([draft, rejected, second])).toEqual([
			{
				timesheet: "TS-3",
				reason: "Wrong project",
				reviewer: "Boss",
				reviewedOn: "",
				hours: 5,
				entries: 2,
			},
		]);
	});
});
