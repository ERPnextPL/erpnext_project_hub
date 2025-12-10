# Copyright (c) 2024, Krzysztof and contributors
# For license information, please see license.txt

import frappe


def on_task_update(doc, method):
	"""
	Update milestone progress when a task is updated.
	Triggered when Task status, milestone assignment changes.
	"""
	# Update current milestone if assigned
	if doc.milestone:
		update_milestone_progress(doc.milestone)

	# If milestone changed, update the old milestone too
	if doc.has_value_changed("milestone"):
		old_milestone = doc.get_doc_before_save()
		if old_milestone and old_milestone.milestone:
			update_milestone_progress(old_milestone.milestone)


def on_task_trash(doc, method):
	"""
	Update milestone progress when a task is deleted.
	"""
	if doc.milestone:
		# Use db_set to avoid recursion
		frappe.db.set_value("Task", doc.name, "milestone", None)
		update_milestone_progress(doc.milestone)


def update_milestone_progress(milestone_name):
	"""
	Recalculate milestone progress based on linked tasks.
	"""
	if not milestone_name:
		return

	if not frappe.db.exists("Project Milestone", milestone_name):
		return

	total_tasks = frappe.db.count("Task", {"milestone": milestone_name})
	completed_tasks = frappe.db.count(
		"Task", {"milestone": milestone_name, "status": "Completed"}
	)

	progress = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

	# Determine new status
	milestone = frappe.get_doc("Project Milestone", milestone_name)
	old_status = milestone.status

	if milestone.status not in ["Completed", "Cancelled"]:
		if progress == 100 and total_tasks > 0:
			new_status = "Completed"
		elif progress > 0:
			new_status = "In Progress"
		else:
			new_status = "Open"
	else:
		new_status = old_status

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
