# Copyright (c) 2024, Krzysztof and contributors
# For license information, please see license.txt

import frappe


def on_task_update(doc, method):
	"""
	Update milestone progress when a task is updated.
	Triggered when Task status, milestone assignment changes.
	Propagates dependency status changes to dependent tasks.
	"""
	# Update current milestone if assigned
	if doc.milestone:
		update_milestone_progress(doc.milestone)

	# If milestone changed, update the old milestone too
	if doc.has_value_changed("milestone"):
		old_milestone = doc.get_doc_before_save()
		if old_milestone and old_milestone.milestone:
			update_milestone_progress(old_milestone.milestone)

	# Propagate status change to tasks that depend on this task
	if doc.has_value_changed("status"):
		_update_dependent_tasks(doc.name)


def sync_progress_from_dependencies(doc, method):
	"""
	Recalculate progress and auto-complete status from the 'Depends On' table.
	"""
	if not doc.depends_on:
		return

	total = len(doc.depends_on)
	completed = 0
	cancelled = 0
	unresolved = 0

	# Collect all dependency task names
	dependency_names = [row.task for row in doc.depends_on if row.task]
	if not dependency_names:
		return

	# Fetch all dependencies in a single query
	tasks = frappe.get_all("Task", filters={"name": ["in", dependency_names]}, fields=["name", "status"])
	resolved_tasks = {task["name"]: task["status"] for task in tasks}

	# Count statuses
	for row in doc.depends_on:
		if row.task:
			if row.task in resolved_tasks:
				status = resolved_tasks[row.task]
				if status == "Completed":
					completed += 1
				elif status == "Cancelled":
					cancelled += 1
			else:
				unresolved += 1
				frappe.log_error(f"Task {row.task} not found", "Subtask Progress Update")

	# Exclude cancelled and unresolved (deleted) dependencies from total
	effective_total = total - cancelled - unresolved

	if effective_total > 0:
		percent = int((completed / effective_total) * 100)
	else:
		percent = 0  # jeśli wszystkie anulowane, postęp = 0

	doc.progress = percent

	# Auto-update status based on progress, keeping progress and status consistent
	if percent == 100:
		if doc.status != "Completed":
			doc.status = "Completed"
	elif percent > 0:
		# Progress started but not complete → Working (even if manually set to Completed)
		if doc.status not in ["Working", "Cancelled"]:
			doc.status = "Working"
	else:
		# No progress → Open (even if manually set to Completed)
		if doc.status not in ["Open", "Cancelled"]:
			doc.status = "Open"


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


def _update_dependent_tasks(task_name):
	"""
	Find all tasks that depend on the given task and recalculate their progress.
	This ensures that when a prerequisite task changes status, all dependent tasks
	are automatically updated.
	"""
	dependent_tasks = frappe.get_all(
		"Task Depends On",
		filters={"task": task_name},
		fields=["parent"],
	)

	for row in dependent_tasks:
		try:
			dependent_task = frappe.get_doc("Task", row.parent)
			sync_progress_from_dependencies(dependent_task, None)
			dependent_task.save(ignore_permissions=True)
		except (frappe.DoesNotExistError, Exception) as e:
			frappe.log_error(
				f"Error updating dependent task {row.parent}: {e!s}",
				"Dependent Task Update",
			)
