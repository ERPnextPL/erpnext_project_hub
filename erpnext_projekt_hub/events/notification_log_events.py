# Copyright (c) 2024, Krzysztof and contributors
# For license information, please see license.txt

from urllib.parse import quote

import frappe
from frappe.utils import get_url


def before_insert(doc, method):
	"""
	Point Task assignment notifications at Project Hub instead of the Desk form.

	Frappe uses Notification Log.link (when set) both for the bell dropdown and
	for the "Open" button in the notification email.
	"""
	if doc.type != "Assignment" or doc.document_type != "Task" or not doc.document_name or doc.link:
		return

	doc.link = get_project_hub_task_url(doc.document_name)


def get_project_hub_task_url(task_name: str) -> str:
	project = frappe.db.get_value("Task", task_name, "project")
	if project:
		path = f"/project-hub/{quote(project, safe='')}/{quote(task_name, safe='')}"
	else:
		# Tasks without a project are reachable only from My Tasks
		path = f"/project-hub/my-tasks?task={quote(task_name, safe='')}"

	return get_url(path)
