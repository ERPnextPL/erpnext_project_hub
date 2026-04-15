"""
Task event handlers for milestone progress tracking.

When a task is updated or deleted, update the associated milestone's progress.
"""

import frappe


def before_validate_task(doc, method=None):
	"""
	Compatibility hook for Task.before_validate.

	Keep this function defined because hooks.py points to it during Task insert/save.
	"""
	return


def validate_task_due_dates(doc, method=None):
	"""
	Compatibility hook for Task.validate.

	Currently reserved for future due-date checks and kept as a no-op to avoid
	broken saves when the hook is triggered.
	"""
	return


def on_task_update(doc, method):
	"""
	Update milestone progress when a task is updated.

	Called on Task.on_update event.
	"""
	if hasattr(doc, "milestone") and doc.milestone:
		update_milestone_progress(doc.milestone)

	# If milestone changed, also update the old one
	if hasattr(doc, "_doc_before_save") and doc._doc_before_save:
		old_milestone = doc._doc_before_save.get("milestone")
		if old_milestone and old_milestone != doc.milestone:
			update_milestone_progress(old_milestone)


def on_task_trash(doc, method):
	"""
	Prepare for task deletion.

	Called on Task.on_trash event.
	"""
	return


def on_task_after_delete(doc, method=None):
	"""
	Update milestone progress after a task is deleted.

	Called on Task.after_delete event.
	"""
	if hasattr(doc, "milestone") and doc.milestone:
		update_milestone_progress(doc.milestone)


def update_milestone_progress(milestone_name):
	"""
	Recalculate and update a milestone's progress fields.

	Queries all tasks linked to the milestone and updates:
	- total_tasks
	- completed_tasks
	- progress
	- status (auto-advance if needed)

	Uses Frappe standard "Completed" status (synchronized with erpnext_projekt_hub).
	"""
	if not frappe.db.exists("Project Milestone", milestone_name):
		return

	milestone = frappe.get_doc("Project Milestone", milestone_name)
	milestone.update_statistics()

	# Determine new status based on progress
	if milestone.status not in ["Completed", "Cancelled"]:
		if milestone.progress == 100 and milestone.total_tasks > 0:
			new_status = "Completed"
		elif milestone.progress > 0:
			new_status = "In Progress"
		else:
			new_status = "Open"
	else:
		new_status = milestone.status

	# Use db_set to avoid triggering validate and other hooks
	frappe.db.set_value(
		"Project Milestone",
		milestone_name,
		{
			"total_tasks": milestone.total_tasks,
			"completed_tasks": milestone.completed_tasks,
			"progress": milestone.progress,
			"status": new_status,
		},
		update_modified=False,
	)
