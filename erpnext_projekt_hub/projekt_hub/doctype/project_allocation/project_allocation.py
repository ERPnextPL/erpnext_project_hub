import frappe
from frappe import _
from frappe.model.document import Document


class ProjectAllocation(Document):
	def validate(self):
		if self.hours is None or self.hours < 0:
			frappe.throw(_("Hours must be a non-negative number"))

		if self.hours > 24:
			frappe.throw(_("Hours cannot exceed 24 per day"))

		# Warn (not block) if total allocations for the day exceed capacity
		self._check_daily_overallocation()

	def _check_daily_overallocation(self):
		"""Log a warning if the employee's total allocations for this day exceed 24h."""
		existing = frappe.db.sql(
			"""
            SELECT SUM(hours)
            FROM `tabProject Allocation`
            WHERE employee = %(employee)s
              AND allocation_date = %(date)s
              AND name != %(name)s
            """,
			{"employee": self.employee, "date": self.allocation_date, "name": self.name or ""},
			as_list=True,
		)
		existing_hours = float((existing or [[0]])[0][0] or 0)
		if existing_hours + self.hours > 24:
			frappe.msgprint(
				_("Total allocations for {0} on {1} will exceed 24 hours.").format(
					self.employee, self.allocation_date
				),
				indicator="orange",
				alert=True,
			)
