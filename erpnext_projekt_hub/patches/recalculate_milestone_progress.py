from __future__ import annotations

import frappe


def execute():
	"""Recalculate all milestone progress excluding Cancelled tasks.

	Fixes stale stored values from before the Cancelled-task exclusion was added.
	"""
	milestones = frappe.get_all(
		"Project Milestone",
		fields=["name"],
		limit_page_length=0,
	)

	for milestone in milestones:
		name = milestone.name
		total_tasks = frappe.db.count("Task", {"milestone": name, "status": ["!=", "Cancelled"]})
		completed_tasks = frappe.db.count("Task", {"milestone": name, "status": "Completed"})

		if total_tasks > 0:
			progress = int((completed_tasks / total_tasks) * 100)
		else:
			progress = 0

		current_status = frappe.db.get_value("Project Milestone", name, "status")
		if current_status not in ["Completed", "Cancelled"]:
			if progress == 100 and total_tasks > 0:
				new_status = "Completed"
			elif progress > 0:
				new_status = "In Progress"
			else:
				new_status = "Open"
		else:
			new_status = current_status

		frappe.db.set_value(
			"Project Milestone",
			name,
			{
				"total_tasks": total_tasks,
				"completed_tasks": completed_tasks,
				"progress": progress,
				"status": new_status,
			},
			update_modified=False,
		)
