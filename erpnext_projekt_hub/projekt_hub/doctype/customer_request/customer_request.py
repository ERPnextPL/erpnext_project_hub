import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, strip_html

from erpnext_projekt_hub.request_queue import sync_analysis_assignment

QUOTED_STATE = "Quoted"

# Quotation can be linked only once the request has been quoted, not during analysis.
STATES_WITHOUT_QUOTATION = ("Draft", "To Analyze")


class CustomerRequest(Document):
	def validate(self):
		self.validate_project_customer()
		self.validate_quotation_state()
		self.validate_quote_has_estimate()
		self.set_state_changed_on()

	def on_update(self):
		sync_analysis_assignment(self)

	def validate_quote_has_estimate(self):
		"""A request can only be marked Quoted once its analysis is written."""
		if self.workflow_state != QUOTED_STATE or not self.has_value_changed("workflow_state"):
			return

		missing = []
		if not strip_html(self.analysis or "").strip():
			missing.append(_("Analysis"))
		if not self.estimated_hours:
			missing.append(_("Estimated Hours"))
		if missing:
			frappe.throw(
				_("Fill in {0} before marking the request as quoted.").format(", ".join(missing)),
				title=_("Analysis incomplete"),
			)

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

	def validate_quotation_state(self):
		if not self.quotation or not self.has_value_changed("quotation"):
			return

		if (self.workflow_state or "Draft") in STATES_WITHOUT_QUOTATION:
			frappe.throw(_("Quotation can be linked only after the Customer Request has been quoted."))

	@frappe.whitelist()
	def create_change_request(self):
		frappe.db.sql(
			"select name from `tabCustomer Request` where name = %s for update",
			self.name,
		)
		self.reload()

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

		state_changed_on = now_datetime()
		frappe.db.set_value(
			self.doctype,
			self.name,
			{
				"change_request": change_request.name,
				"workflow_state": "Converted",
				"state_changed_on": state_changed_on,
			},
			update_modified=False,
		)
		self.change_request = change_request.name
		self.workflow_state = "Converted"
		self.state_changed_on = state_changed_on

		return change_request.name
