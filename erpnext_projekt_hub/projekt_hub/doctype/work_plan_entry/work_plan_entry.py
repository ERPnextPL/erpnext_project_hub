import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from erpnext_projekt_hub.access import can_plan_for_others, get_own_employee

MAX_HOURS_PER_ENTRY = 24


class WorkPlanEntry(Document):
	"""Hours an employee is planned to work on a project on one day (Projekt HUB work planning)."""

	def validate(self):
		self.hours = flt(self.hours, 2)
		if self.hours <= 0 or self.hours > MAX_HOURS_PER_ENTRY:
			frappe.throw(
				_("Planned hours must be greater than 0 and at most {0}").format(MAX_HOURS_PER_ENTRY)
			)

		duplicate = frappe.db.exists(
			"Work Plan Entry",
			{
				"employee": self.employee,
				"date": self.date,
				"project": self.project,
				"name": ("!=", self.name),
			},
		)
		if duplicate:
			frappe.throw(
				_("{0} is already planned on project {1} on {2}").format(
					self.employee_name or self.employee, self.project, frappe.format(self.date, "Date")
				),
				frappe.DuplicateEntryError,
			)


def has_permission(doc, ptype="read", user=None, debug=False) -> bool:
	"""Keep everybody who is not a planner on the rows of their own Employee record.

	A controller hook can only deny, never grant, so the DocType's role permissions
	stay in charge of who may write at all: this narrows every access type to one's
	own plan, so one employee can neither see nor change another one's days.
	"""
	if can_plan_for_others(user):
		return True

	own_employee = get_own_employee(user)
	return bool(own_employee) and doc.employee == own_employee


def get_permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""Restrict list views and reports the same way has_permission() restricts documents."""
	if can_plan_for_others(user):
		return ""

	own_employee = get_own_employee(user)
	if not own_employee:
		return "1 = 0"

	return f"`tabWork Plan Entry`.`employee` = {frappe.db.escape(own_employee)}"
