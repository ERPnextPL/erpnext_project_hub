import frappe
from frappe.desk.form.assign_to import add as add_assignment
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.patches.post_model_sync.setup_customer_change_requests import (
	UNASSIGNED_ANALYSIS_FILTERS,
)
from erpnext_projekt_hub.projekt_hub.doctype.customer_request.test_customer_request import (
	create_project,
	get_or_create_customer,
)
from erpnext_projekt_hub.request_queue import release_analysis, take_for_analysis

test_ignore = ["Customer", "Project", "Quotation", "Task"]


def create_request_to_analyze(project, customer, subject):
	customer_request = frappe.get_doc(
		{
			"doctype": "Customer Request",
			"customer": customer,
			"project": project,
			"subject": subject,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value(
		"Customer Request", customer_request.name, "workflow_state", "To Analyze", update_modified=False
	)
	return frappe.get_doc("Customer Request", customer_request.name)


def assign(customer_request, user="Administrator"):
	add_assignment({"doctype": "Customer Request", "name": customer_request.name, "assign_to": [user]})


class TestCustomerRequestAnalysisQueue(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.customer = get_or_create_customer()
		self.project = create_project(self.customer)

	def test_quoting_requires_analysis_and_estimate(self):
		customer_request = create_request_to_analyze(self.project, self.customer, "_Test quote check")

		customer_request.workflow_state = "Quoted"
		with self.assertRaises(frappe.ValidationError):
			customer_request.save()

		customer_request.reload()
		customer_request.workflow_state = "Quoted"
		customer_request.analysis = "<p>_Test analysis</p>"
		customer_request.estimated_hours = 4
		customer_request.save()

		self.assertEqual(
			frappe.db.get_value("Customer Request", customer_request.name, "workflow_state"), "Quoted"
		)

	def test_leaving_analysis_closes_assignments(self):
		customer_request = create_request_to_analyze(self.project, self.customer, "_Test close assignment")
		assign(customer_request)

		customer_request.reload()
		customer_request.workflow_state = "Quoted"
		customer_request.analysis = "<p>_Test analysis</p>"
		customer_request.estimated_hours = 2
		customer_request.save()

		open_todos = frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "Customer Request",
				"reference_name": customer_request.name,
				"status": "Open",
			},
		)
		self.assertEqual(open_todos, [])

	def test_unassigned_queue_includes_released_requests(self):
		never_taken = create_request_to_analyze(self.project, self.customer, "_Test never taken")
		taken = create_request_to_analyze(self.project, self.customer, "_Test taken")
		released = create_request_to_analyze(self.project, self.customer, "_Test released")
		take_for_analysis("Customer Request", taken.name)
		take_for_analysis("Customer Request", released.name)
		release_analysis("Customer Request", released.name)

		unassigned = frappe.get_list(
			"Customer Request",
			filters=[*UNASSIGNED_ANALYSIS_FILTERS, ["Customer Request", "project", "=", self.project]],
			pluck="name",
		)

		self.assertCountEqual(unassigned, [never_taken.name, released.name])

	def test_workflow_lets_projects_users_analyze_and_never_marks_converted(self):
		workflow = frappe.get_doc("Workflow", "Customer Request Workflow")

		analysis_editors = {row.allow_edit for row in workflow.states if row.state == "To Analyze"}
		self.assertIn("Projects User", analysis_editors)
		self.assertNotIn("Converted", {row.next_state for row in workflow.transitions})
