import frappe
from frappe import _
from frappe.model.document import Document


class CustomerRequest(Document):
	def validate(self):
		self.validate_project_customer()

	def validate_project_customer(self):
		if not self.project or not self.customer:
			return

		project_customer = frappe.db.get_value("Project", self.project, "customer")
		if project_customer and project_customer != self.customer:
			frappe.throw(_("Customer must match the customer assigned to project {0}.").format(self.project))

	@frappe.whitelist()
	def create_change_request(self):
		if self.change_request:
			frappe.throw(
				_("Change Request {0} already exists for this Customer Request.").format(self.change_request)
			)

		if self.workflow_state not in ("Accepted", "Converted"):
			frappe.throw(_("Customer Request must be accepted before creating a Change Request."))

		change_request = frappe.get_doc(
			{
				"doctype": "Change Request",
				"customer_request": self.name,
				"customer": self.customer,
				"project": self.project,
				"subject": self.subject,
				"approved_scope": self.analysis or self.notes,
				"approved_hours": self.estimated_hours,
				"approved_amount": self.estimated_amount,
				"currency": self.currency,
				"quotation": self.quotation,
			}
		)
		change_request.insert()

		frappe.db.set_value(
			self.doctype,
			self.name,
			{
				"change_request": change_request.name,
				"workflow_state": "Converted",
			},
			update_modified=False,
		)
		self.change_request = change_request.name
		self.workflow_state = "Converted"

		return change_request.name
