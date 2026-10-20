import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.projekt_hub.doctype.customer_request.test_customer_request import (
	create_project,
	get_or_create_customer,
)
from erpnext_projekt_hub.request_queue import attach_file, release_analysis, take_for_analysis

test_ignore = ["Customer", "Project", "Quotation", "Task"]

ANALYST = "request-analyst@example.com"
OTHER_ANALYST = "request-analyst-2@example.com"
PROJECT_MANAGER = "request-project-manager@example.com"


def make_user(email, *roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	frappe.get_doc("User", email).add_roles(*roles)


def open_assignees(doctype, name):
	return frappe.get_all(
		"ToDo",
		filters={"reference_type": doctype, "reference_name": name, "status": "Open"},
		pluck="allocated_to",
	)


def upload_file(content=b"_Test attachment"):
	return frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"_test_{frappe.generate_hash(length=6)}.txt",
			"content": content,
			"is_private": 1,
		}
	).insert()


class TestRequestQueue(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_user(ANALYST, "Projects User")
		make_user(OTHER_ANALYST, "Projects User")
		make_user(PROJECT_MANAGER, "Project Manager")
		self.customer = get_or_create_customer()
		self.project = create_project(self.customer)

	def tearDown(self):
		frappe.set_user("Administrator")

	def create_customer_request(self, subject, state="To Analyze"):
		request = frappe.get_doc(
			{
				"doctype": "Customer Request",
				"customer": self.customer,
				"project": self.project,
				"subject": subject,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("Customer Request", request.name, "workflow_state", state, update_modified=False)
		return frappe.get_doc("Customer Request", request.name)

	def create_change_request(self, subject):
		return frappe.get_doc(
			{
				"doctype": "Change Request",
				"customer": self.customer,
				"project": self.project,
				"subject": subject,
				"approved_scope": "_Test scope",
				"approved_hours": 2,
			}
		).insert(ignore_permissions=True)

	def test_taking_records_the_analyst_and_blocks_others(self):
		request = self.create_customer_request("_Test take records analyst")

		frappe.set_user(ANALYST)
		take_for_analysis("Customer Request", request.name)
		self.assertEqual(frappe.db.get_value("Customer Request", request.name, "analyst"), ANALYST)
		self.assertEqual(open_assignees("Customer Request", request.name), [ANALYST])

		frappe.set_user(OTHER_ANALYST)
		with self.assertRaises(frappe.ValidationError):
			take_for_analysis("Customer Request", request.name)
		with self.assertRaises(frappe.ValidationError):
			release_analysis("Customer Request", request.name)

		frappe.set_user(ANALYST)
		release_analysis("Customer Request", request.name)
		self.assertFalse(frappe.db.get_value("Customer Request", request.name, "analyst"))
		self.assertEqual(open_assignees("Customer Request", request.name), [])

	def test_setting_the_analyst_field_moves_the_assignment(self):
		request = self.create_customer_request("_Test analyst field")

		request.analyst = ANALYST
		request.save()
		self.assertEqual(open_assignees("Customer Request", request.name), [ANALYST])

		request.reload()
		request.analyst = OTHER_ANALYST
		request.save()
		self.assertEqual(open_assignees("Customer Request", request.name), [OTHER_ANALYST])

	def test_leaving_analysis_keeps_the_analyst(self):
		request = self.create_customer_request("_Test analyst kept")
		take_for_analysis("Customer Request", request.name)

		request.reload()
		request.workflow_state = "Quoted"
		request.analysis = "<p>_Test analysis</p>"
		request.estimated_hours = 3
		request.save()

		self.assertEqual(frappe.db.get_value("Customer Request", request.name, "analyst"), "Administrator")
		self.assertEqual(open_assignees("Customer Request", request.name), [])

		with self.assertRaises(frappe.ValidationError):
			release_analysis("Customer Request", request.name)
		self.assertEqual(frappe.db.get_value("Customer Request", request.name, "analyst"), "Administrator")

	def test_change_request_is_taken_while_draft(self):
		change_request = self.create_change_request("_Test change request analysis")

		frappe.set_user(ANALYST)
		take_for_analysis("Change Request", change_request.name)
		self.assertEqual(frappe.db.get_value("Change Request", change_request.name, "analyst"), ANALYST)
		self.assertEqual(open_assignees("Change Request", change_request.name), [ANALYST])

		frappe.set_user("Administrator")
		change_request.reload()
		apply_workflow(change_request, "Approve")
		self.assertEqual(open_assignees("Change Request", change_request.name), [])

		frappe.set_user(OTHER_ANALYST)
		with self.assertRaises(frappe.ValidationError):
			take_for_analysis("Change Request", change_request.name)

	def test_readers_can_attach_files(self):
		# Projects User may only read Change Requests, and Quoted Customer Requests
		# are edited by managers only.
		change_request = self.create_change_request("_Test change request attachment")
		quoted_request = self.create_customer_request("_Test quoted attachment", state="Quoted")

		frappe.set_user(ANALYST)
		self.assertFalse(frappe.has_permission("Change Request", "write", change_request.name))
		for doctype, name in (
			("Change Request", change_request.name),
			("Customer Request", quoted_request.name),
		):
			uploaded = upload_file()
			attach_file(doctype, name, uploaded.name)
			self.assertEqual(
				frappe.db.get_value("File", uploaded.name, ["attached_to_doctype", "attached_to_name"]),
				(doctype, name),
			)

	def test_only_own_unattached_files_can_be_attached(self):
		request = self.create_customer_request("_Test foreign attachment")

		frappe.set_user(OTHER_ANALYST)
		foreign = upload_file()

		frappe.set_user(ANALYST)
		with self.assertRaises(frappe.PermissionError):
			attach_file("Customer Request", request.name, foreign.name)

		own = upload_file()
		attach_file("Customer Request", request.name, own.name)
		with self.assertRaises(frappe.PermissionError):
			attach_file("Customer Request", request.name, own.name)

	def test_project_manager_can_work_on_all_requests(self):
		request = self.create_customer_request("_Test project manager access")
		change_request = self.create_change_request("_Test project manager change")

		for doctype, name in (
			("Customer Request", request.name),
			("Change Request", change_request.name),
		):
			self.assertTrue(frappe.has_permission(doctype, "read", name, user=PROJECT_MANAGER))
			self.assertTrue(frappe.has_permission(doctype, "write", name, user=PROJECT_MANAGER))

		workflow = frappe.get_doc("Workflow", "Customer Request Workflow")
		quote_roles = {row.allowed for row in workflow.transitions if row.action == "Mark Quoted"}
		self.assertIn("Project Manager", quote_roles)
