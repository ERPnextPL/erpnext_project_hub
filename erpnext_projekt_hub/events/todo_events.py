import frappe
from frappe import _
from frappe.utils import escape_html, getdate, strip_html, today


def set_task_assignment_description(doc, method=None):
	"""Replace Frappe's generic "Assignment for Task TASK-..." ToDo description
	with the task subject and project name, so the ToDo reads like the task."""
	if doc.reference_type != "Task" or not doc.reference_name:
		return

	description = strip_html(doc.description or "").strip()
	default_descriptions = {
		_("Assignment for {0} {1}").format("Task", doc.reference_name),
		f"Assignment for Task {doc.reference_name}",
	}
	if description and description not in default_descriptions:
		return

	task = frappe.db.get_value("Task", doc.reference_name, ["subject", "project"], as_dict=True)
	if not task or not task.subject:
		return

	text = task.subject
	if task.project:
		project_name = frappe.db.get_value("Project", task.project, "project_name") or task.project
		text = f"{task.subject} ({project_name})"

	doc.description = escape_html(text)


def set_task_assignment_date(doc, method=None):
	"""Default the ToDo date to the task's expected end date instead of the
	day the assignment was made."""
	if doc.reference_type != "Task" or not doc.reference_name:
		return
	if doc.date and getdate(doc.date) != getdate(today()):
		return

	exp_end_date = frappe.db.get_value("Task", doc.reference_name, "exp_end_date")
	if exp_end_date:
		doc.date = exp_end_date


def sync_task_todo_dates(task_name, exp_end_date):
	"""Move the date of open assignments when the task's expected end date changes."""
	frappe.db.set_value(
		"ToDo",
		{"reference_type": "Task", "reference_name": task_name, "status": "Open"},
		"date",
		exp_end_date or None,
	)
