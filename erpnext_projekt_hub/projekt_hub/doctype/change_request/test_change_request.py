import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.projekt_hub.doctype.customer_request.test_customer_request import (
	create_project,
	get_or_create_customer,
)


class TestChangeRequest(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_approved_change_request_creates_single_project_task(self):
		customer = get_or_create_customer()
		project = create_project(customer)
		change_request = frappe.get_doc(
			{
				"doctype": "Change Request",
				"customer": customer,
				"project": project,
				"subject": "_Test Approved dashboard change",
				"approved_scope": "_Test build dedicated dashboard",
				"approved_hours": 8,
			}
		).insert(ignore_permissions=True)
		apply_workflow(change_request, "Approve")

		change_request.reload()
		self.assertEqual(change_request.workflow_state, "Task Created")
		self.assertTrue(change_request.task)

		task = frappe.get_doc("Task", change_request.task)
		self.assertEqual(task.project, project)
		self.assertEqual(task.subject, change_request.subject)
		self.assertEqual(task.status, "Open")
		self.assertEqual(task.expected_time, 8)
		self.assertEqual(task.description, change_request.approved_scope)
		self.assertEqual(task.change_request, change_request.name)

		first_task = change_request.task
		change_request.save(ignore_permissions=True)
		change_request.reload()

		self.assertEqual(change_request.task, first_task)
		self.assertEqual(frappe.db.count("Task", {"change_request": change_request.name}), 1)
