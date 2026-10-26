import frappe
from frappe import _
from frappe.desk.form.assign_to import add as add_assignment
from frappe.model.document import Document
from frappe.utils import now_datetime

from erpnext_projekt_hub.request_queue import sync_request_assignment


class ChangeRequest(Document):
	def validate(self):
		self.validate_project_customer()
		self.validate_customer_request()
		self.validate_realization_assignee()
		self.set_state_changed_on()

	def on_update(self):
		sync_request_assignment(self)
		if self.workflow_state == "Approved" and not self.task:
			self.create_project_task()

	def validate_realization_assignee(self):
		if self.workflow_state == "Approved" and not self.realization_assignee:
			frappe.throw(_("Assign a person for realization before approving the change request."))

		previous = self.get_doc_before_save()
		if previous and previous.task and self.realization_assignee != previous.realization_assignee:
			frappe.throw(_("Change the implementer on the linked project task after it has been created."))

	def set_state_changed_on(self):
		"""Remember when the request entered its workflow state (requests board ageing)."""
		if self.has_value_changed("workflow_state") or not self.state_changed_on:
			self.state_changed_on = now_datetime()

	def validate_project_customer(self):
		if not self.project or not self.customer:
			return

		project_customer = frappe.db.get_value("Project", self.project, "customer")
		if project_customer and project_customer != self.customer:
			frappe.throw(_("Customer must match the customer assigned to project {0}.").format(self.project))

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
		add_assignment(
			{
				"doctype": "Task",
				"name": task.name,
				"assign_to": [self.realization_assignee],
				"description": task.subject,
			}
		)
		self.db_set(
			{
				"task": task.name,
				"workflow_state": "Task Created",
				"state_changed_on": now_datetime(),
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
