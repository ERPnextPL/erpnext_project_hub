# Copyright (c) 2024, Krzysztof and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import format_date, getdate


def before_validate_task(doc, method):
	"""
	Check task due date against project end date before ERPNext's own validation,
	so we can show a user-friendly message instead of a technical exception.
	"""
	if not doc.exp_end_date or not doc.project:
		return

	project_end_date = frappe.db.get_value("Project", doc.project, "expected_end_date")
	if project_end_date and getdate(doc.exp_end_date) > getdate(project_end_date):
		frappe.throw(
			_(
				"Task due date {0} cannot be later than the project's end date {1}. "
				"Please adjust the task date or update the project's end date first."
			).format(
				frappe.bold(format_date(doc.exp_end_date)),
				frappe.bold(format_date(project_end_date)),
			),
			title=_("Invalid Date"),
		)


def validate_task_due_dates(doc, method):
	"""
	Walidacja daty zakończenia (exp_end_date) dla hierarchii zadań.

	Scenariusz 1: Jeśli zmienia się data podrzędnego na datę później niż parent,
	automatycznie aktualizuje datę parent i wyświetla komunikat.

	Scenariusz 2: Jeśli zmienia się data parent na wcześniejszą niż którekolwiek child,
	wyrzuca błąd z komunikatem.
	"""
	if not doc.exp_end_date:
		return

	# Scenariusz 1: Zadanie podrzędne ma datę późniejszą niż parent
	if doc.parent_task:
		parent_exp_end_date = frappe.db.get_value("Task", doc.parent_task, "exp_end_date")
		if parent_exp_end_date:
			if getdate(doc.exp_end_date) > getdate(parent_exp_end_date):
				# Use max date across all siblings (from DB) + current doc's date,
				# so parent validation doesn't fail due to another sibling with a later date.
				siblings = frappe.get_all(
					"Task",
					filters={"parent_task": doc.parent_task, "name": ["!=", doc.name]},
					fields=["exp_end_date"],
				)
				max_date = max(
					[getdate(s.exp_end_date) for s in siblings if s.exp_end_date]
					+ [getdate(doc.exp_end_date)]
				)

				parent_doc = frappe.get_doc("Task", doc.parent_task)
				parent_doc.exp_end_date = str(max_date)
				parent_doc.flags.ignore_recursion_check = True
				parent_doc.save()

				# Pokaż komunikat
				frappe.msgprint(
					_(
						"Due date of parent task '{0}' has been automatically updated "
						"to {1} because subtask '{2}' has a later due date."
					).format(
						frappe.bold(doc.parent_task),
						frappe.bold(format_date(max_date)),
						frappe.bold(doc.name),
					),
					title=_("Date updated"),
					indicator="green",
				)

	# Scenariusz 2: Sprawdzenie czy data parent nie jest wcześniejsza od zadań podrzędnych
	if not doc.is_group:
		return

	child_tasks = frappe.get_all(
		"Task",
		filters={"parent_task": doc.name},
		fields=["name", "exp_end_date"],
		order_by="exp_end_date desc",
	)

	if not child_tasks:
		return

	for child in child_tasks:
		if child.exp_end_date and getdate(doc.exp_end_date) < getdate(child.exp_end_date):
			frappe.throw(
				_(
					"Parent task due date cannot be earlier than a subtask due date. "
					"Subtask '{0}' has due date {1}, while parent task due date is {2}."
				).format(
					frappe.bold(child.name),
					frappe.bold(format_date(child.exp_end_date)),
					frappe.bold(format_date(doc.exp_end_date)),
				)
			)


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
	remove_from_parent_depends_on(doc)

	if doc.milestone:
		# Use db_set to avoid recursion
		frappe.db.set_value("Task", doc.name, "milestone", None)
		update_milestone_progress(doc.milestone)


def remove_from_parent_depends_on(doc):
	"""
	Remove the task from its parent's depends_on table before deletion,
	to avoid broken references.
	"""
	if not doc.parent_task:
		return

	parent = frappe.get_doc("Task", doc.parent_task)
	original_len = len(parent.depends_on)
	parent.depends_on = [row for row in parent.depends_on if row.task != doc.name]

	if len(parent.depends_on) < original_len:
		parent.flags.ignore_recursion_check = True
		parent.save()


def update_milestone_progress(milestone_name):
	"""
	Recalculate milestone progress based on linked tasks.
	"""
	if not milestone_name:
		return

	if not frappe.db.exists("Project Milestone", milestone_name):
		return

	total_tasks = frappe.db.count("Task", {"milestone": milestone_name})
	completed_tasks = frappe.db.count("Task", {"milestone": milestone_name, "status": "Completed"})

	progress = int(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

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
