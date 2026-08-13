# Copyright (c) 2024, Krzysztof and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

# A subtask in one of these statuses is no longer finished. A parent that is
# already Completed cannot honestly stay Completed once one of its subtasks
# moves back to any of them.
REOPENED_STATUSES = ("Open", "Working", "Pending Review", "Overdue")

# Status a Completed parent falls back to when that happens.
REOPENED_PARENT_STATUS = "Working"


def on_task_update(doc, method=None):
	"""Keep milestone statistics and the parent task chain in sync.

	Subtask changes never dictate the parent's status. The only exception is a
	parent sitting on Completed while one of its subtasks goes back to an open
	status, or while a new subtask is added underneath it - a finished task
	cannot contain unfinished work, so it drops to Working.
	"""
	if doc.milestone:
		update_milestone_progress(doc.milestone)

	# If milestone changed, update the old milestone too
	if doc.has_value_changed("milestone"):
		previous = doc.get_doc_before_save()
		if previous and previous.milestone:
			update_milestone_progress(previous.milestone)

	if doc.flags.ignore_hierarchy_sync:
		return

	_sync_hierarchy(doc)


def on_task_trash(doc, method=None):
	"""
	Update milestone progress and parent progress when a task is deleted.
	"""
	if doc.milestone:
		# Use db_set to avoid recursion
		frappe.db.set_value("Task", doc.name, "milestone", None)
		update_milestone_progress(doc.milestone)

	if doc.parent_task:
		# Deleting a subtask is not one of the cases that may un-complete a
		# parent, so only the roll-up runs here.
		_walk_ancestors(doc.parent_task, reopen=False, exclude=doc.name)


def _sync_hierarchy(doc):
	"""Route a task change to the roll-up over its ancestors."""
	previous = doc.get_doc_before_save()

	# A subtask was added: either the task is brand new, or an existing task was
	# moved underneath a different parent.
	if previous is None or doc.parent_task != previous.parent_task:
		if previous is not None and previous.parent_task:
			# The old parent only loses a subtask, which never touches its status.
			_walk_ancestors(previous.parent_task, reopen=False)

		_walk_ancestors(doc.parent_task, reopen=doc.status in REOPENED_STATUSES)
		return

	if doc.has_value_changed("status"):
		_walk_ancestors(doc.parent_task, reopen=doc.status in REOPENED_STATUSES)


def _walk_ancestors(task_name, reopen, exclude=None):
	"""Roll progress up the parent chain, un-completing ancestors when asked.

	`reopen` carries the right to take a Completed ancestor back to Working. It
	survives one more level only when the ancestor actually left Completed,
	because that is what makes its own parent contain unfinished work again.
	`exclude` leaves a task out of the roll-up, for the on_trash case where the
	row is still present in the database.
	"""
	seen = set()
	current = task_name

	while current and current not in seen:
		seen.add(current)

		ancestor = frappe.db.get_value("Task", current, ["status", "progress", "parent_task"], as_dict=True)
		if not ancestor:
			return

		progress = _subtask_progress(current, exclude=exclude)
		reopened = reopen and ancestor.status == "Completed"

		if reopened:
			_reopen_task(current, progress)
		elif progress is not None and int(flt(ancestor.progress)) != progress:
			frappe.db.set_value("Task", current, "progress", progress, update_modified=False)

		reopen = reopened
		exclude = None
		current = ancestor.parent_task


def _subtask_progress(task_name, exclude=None):
	"""Percentage of a task's subtasks that are Completed.

	Cancelled subtasks drop out of the total. Returns None when the task has no
	subtasks left, so that a leaf task keeps whatever progress a person entered.
	"""
	total_filters = {"parent_task": task_name, "status": ["!=", "Cancelled"]}
	completed_filters = {"parent_task": task_name, "status": "Completed"}

	if exclude:
		total_filters["name"] = ["!=", exclude]
		completed_filters["name"] = ["!=", exclude]

	total = frappe.db.count("Task", total_filters)
	if not total:
		return None

	return int(frappe.db.count("Task", completed_filters) / total * 100)


def _reopen_task(task_name, progress):
	"""Take a Completed task back to Working through a real save.

	The save records the transition in the task's Version history, so the change
	is visible in the timeline instead of appearing out of nowhere. The flag
	stops the resulting on_update from walking the chain a second time - the
	caller already does that. A parent that refuses to save must not block the
	subtask the person is actually editing, so the status is written directly
	as a fallback.
	"""
	try:
		task = frappe.get_doc("Task", task_name)
		task.status = REOPENED_PARENT_STATUS
		if progress is not None:
			task.progress = progress
		task.flags.ignore_hierarchy_sync = True
		task.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Task Hierarchy Sync: {task_name}")

		values = {"status": REOPENED_PARENT_STATUS}
		if progress is not None:
			values["progress"] = progress
		frappe.db.set_value("Task", task_name, values, update_modified=False)


def update_milestone_progress(milestone_name):
	"""
	Recalculate milestone progress based on linked tasks.
	"""
	if not milestone_name:
		return

	if not frappe.db.exists("Project Milestone", milestone_name):
		return

	total_tasks = frappe.db.count("Task", {"milestone": milestone_name, "status": ["!=", "Cancelled"]})
	completed_tasks = frappe.db.count("Task", {"milestone": milestone_name, "status": "Completed"})

	progress = int(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

	# Determine new status based on progress
	milestone = frappe.get_doc("Project Milestone", milestone_name)

	if progress == 100 and total_tasks > 0:
		new_status = "Completed"
	elif progress > 0:
		new_status = "In Progress"
	else:
		new_status = "Open"

	# Preserve Cancelled status
	if milestone.status == "Cancelled":
		new_status = "Cancelled"

	# Update milestone
	frappe.db.set_value(
		"Project Milestone",
		milestone_name,
		{
			"total_tasks": total_tasks,
			"completed_tasks": completed_tasks,
			"progress": progress,
			"status": new_status,
		},
		update_modified=True,
	)
