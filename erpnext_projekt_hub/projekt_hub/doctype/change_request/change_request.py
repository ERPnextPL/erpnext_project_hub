import frappe
from frappe import _
from frappe.model.document import Document


class ChangeRequest(Document):
	def validate(self):
		self.validate_project_customer()
		self.validate_customer_request()

	def on_update(self):
		if self.workflow_state == "Approved" and not self.task:
			self.create_project_task()

	def validate_project_customer(self):
		if not self.project or not self.customer:
			return

		project_customer = frappe.db.get_value("Project", self.project, "customer")
		if project_customer and project_customer != self.customer:
			frappe.throw(
				_("Customer must match the customer assigned to project {0}.").format(self.project)
			)

	def validate_customer_request(self):
		if not self.customer_request:
			return

		customer_request = frappe.db.get_value(
			"Customer Request",
			self.customer_request,
			["customer", "project", "change_request"],
			as_dict=True,
		)
		if not customer_request:
			frappe.throw(_("Customer Request {0} does not exist.").format(self.customer_request))

		if customer_request.customer != self.customer or customer_request.project != self.project:
			frappe.throw(_("Change Request must use the same customer and project as Customer Request."))

		if customer_request.change_request and customer_request.change_request != self.name:
			frappe.throw(
				_("Customer Request {0} is already linked to Change Request {1}.").format(
					self.customer_request, customer_request.change_request
				)
			)

	def create_project_task(self):
		task = frappe.get_doc(
			{
				"doctype": "Task",
				"subject": self.subject,
				"project": self.project,
				"status": "Open",
				"expected_time": self.approved_hours,
				"description": self.approved_scope,
				"change_request": self.name,
			}
		)
		task.insert()

		frappe.db.set_value(
			self.doctype,
			self.name,
			{
				"task": task.name,
				"workflow_state": "Task Created",
			},
			update_modified=False,
		)

		if self.customer_request:
			frappe.db.set_value(
				"Customer Request",
				self.customer_request,
				"change_request",
				self.name,
				update_modified=False,
			)
