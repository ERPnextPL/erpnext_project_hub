# Copyright (c) 2024, Krzysztof and contributors
# For license information, please see license.txt

import frappe
from erpnext.projects.doctype.task.task import Task
from frappe import _
from frappe.utils import getdate, today

# Statuses in which a missed due date no longer matters.
CLOSED_STATUSES = ("Completed", "Cancelled", "Template")


class HubTask(Task):
	"""Task controller tweaks, mixed in via ``extend_doctype_class`` on Frappe v16
	and installed via ``override_doctype_class`` on v15 (see hooks.py)."""

	def validate_status(self):
		if self.status == "Completed":
			previous_status = self.get_db_value("status")
			if previous_status == "Completed":
				if self.has_value_changed("completed_by"):
					frappe.throw(_("Completion attribution cannot be changed after the task is completed."))
			else:
				assigned_users = set(
					frappe.get_all(
						"ToDo",
						filters={
							"reference_type": "Task",
							"reference_name": self.name,
							"status": "Open",
							"allocated_to": ["is", "set"],
						},
						pluck="allocated_to",
					)
				)

				if len(assigned_users) == 1:
					self.completed_by = next(iter(assigned_users))
				elif not assigned_users:
					self.completed_by = frappe.session.user
				elif frappe.session.user in assigned_users:
					self.completed_by = frappe.session.user
				elif self.completed_by not in assigned_users:
					frappe.throw(
						_("Select which assigned person completed this task."),
						title=_("Completion attribution required"),
					)

		super().validate_status()

	def update_status(self):
		"""Flag a missed due date instead of overwriting the status.

		ERPNext's daily ``set_tasks_as_overdue`` job calls this and, upstream,
		replaces the status with "Overdue". That throws away where the task
		really is (e.g. Pending Review), so the Hub keeps the status untouched
		and records the delay in the separate ``hub_is_overdue`` flag.
		"""
		is_overdue = compute_is_overdue(self)
		if self.get("hub_is_overdue") != is_overdue:
			self.db_set("hub_is_overdue", is_overdue, update_modified=False)


def compute_is_overdue(doc):
	if doc.status in CLOSED_STATUSES or not doc.exp_end_date:
		return 0
	return int(getdate(doc.exp_end_date) < getdate(today()))


def set_overdue_flag(doc, method=None):
	"""Keep the flag in step with the due date on every save, so moving the
	date into the future (or closing the task) clears it straight away."""
	doc.hub_is_overdue = compute_is_overdue(doc)
