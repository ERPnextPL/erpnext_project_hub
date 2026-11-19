from __future__ import annotations

import frappe

SCRIPT_NAME = "Sub task update"


def execute():
	"""Delete the "Sub task update" server script - task_events.py owns progress now.

	The script recalculated Task.progress from the Depends On table on every save,
	which fought with the subtask roll-up in events/task_events.py: a task with
	both subtasks and dependencies had its rolled-up progress overwritten by the
	dependency figure on the next save, including the value _reopen_task had just
	written. Progress now comes from one place only - the subtask roll-up - and
	dependencies drive neither progress nor status, matching the way ERPNext
	itself treats the Depends On table.

	Dropping the fixture keeps the script off new sites, but `bench migrate` never
	deletes fixture records that disappeared from an app, so sites that already
	imported it need this patch. The delete leaves a Deleted Document behind, so a
	site that customised the script can still recover its code from there.
	"""
	if not frappe.db.exists("Server Script", SCRIPT_NAME):
		return

	frappe.delete_doc("Server Script", SCRIPT_NAME, ignore_missing=True)
