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


def sync_progress_from_dependencies(doc, method):
	"""
	Recalculate progress and auto-complete status from the 'Depends On' table.
	"""
	if not doc.depends_on:
		return

	total = len(doc.depends_on)
	completed = 0
	cancelled = 0

	for row in doc.depends_on:
		if row.task:
			try:
				task = frappe.get_doc("Task", row.task)
				if task.status == "Completed":
					completed += 1
				elif task.status == "Cancelled":
					cancelled += 1
			except frappe.DoesNotExistError:
				frappe.log_error(f"Task {row.task} not found", "Subtask Progress Update")

	# Odliczamy anulowane od całkowitej liczby
	effective_total = total - cancelled

	if effective_total > 0:
		percent = int((completed / effective_total) * 100)
	else:
		percent = 0  # jeśli wszystkie anulowane, postęp = 0

	doc.progress = percent

	# Automatyczna zmiana statusu głównego zadania
	if percent == 100 and doc.status != "Completed":
		doc.status = "Completed"


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
