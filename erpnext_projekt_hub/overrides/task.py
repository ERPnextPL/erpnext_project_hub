# Copyright (c) 2024, Krzysztof and contributors
# For license information, please see license.txt

from erpnext.projects.doctype.task.task import Task
from frappe.utils import getdate, today

# Statuses in which a missed due date no longer matters.
CLOSED_STATUSES = ("Completed", "Cancelled", "Template")


class HubTask(Task):
	"""Task controller tweaks, mixed in via ``extend_doctype_class`` on Frappe v16
	and installed via ``override_doctype_class`` on v15 (see hooks.py)."""

	def update_status(self):
		"""Flag a missed due date instead of overwriting the status.

		ERPNext's daily ``set_tasks_as_overdue`` job calls this and, upstream,
		replaces the status with "Overdue". That throws away where the task
		really is (e.g. Pending Review), so the Hub keeps the status untouched
		and records the delay in the separate ``is_overdue`` flag.
		"""
		is_overdue = compute_is_overdue(self)
		if self.get("is_overdue") != is_overdue:
			self.db_set("is_overdue", is_overdue, update_modified=False)


def compute_is_overdue(doc):
	if doc.status in CLOSED_STATUSES or not doc.exp_end_date:
		return 0
	return int(getdate(doc.exp_end_date) < getdate(today()))


def set_overdue_flag(doc, method=None):
	"""Keep the flag in step with the due date on every save, so moving the
	date into the future (or closing the task) clears it straight away."""
	doc.is_overdue = compute_is_overdue(doc)
