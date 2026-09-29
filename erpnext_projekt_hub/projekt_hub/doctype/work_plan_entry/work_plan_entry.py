import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

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
