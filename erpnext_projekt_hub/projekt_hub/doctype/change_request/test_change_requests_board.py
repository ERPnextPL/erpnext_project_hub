import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import get_datetime

from erpnext_projekt_hub.api.project_hub import apply_change_request_action, get_project_requests
from erpnext_projekt_hub.patches.post_model_sync import backfill_change_request_state_changed_on
from erpnext_projekt_hub.projekt_hub.doctype.customer_request.test_customer_request import (
	create_project,
	get_or_create_customer,
)

test_ignore = ["Customer", "Project", "Quotation", "Task"]

OLD_TIMESTAMP = "2026-01-01 08:00:00"


def create_change_request(project, customer, subject):
	return frappe.get_doc(
		{
			"doctype": "Change Request",
			"customer": customer,
			"project": project,
			"subject": subject,
			"approved_scope": "_Test approved scope",
			"approved_hours": 5,
			"realization_assignee": "Administrator",
		}
	).insert(ignore_permissions=True)


def board_row(project, name):
	return next(row for row in get_project_requests(project)["change_requests"] if row.name == name)


class TestChangeRequestsBoard(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.customer = get_or_create_customer()
		self.project = create_project(self.customer)

	def test_draft_row_offers_approval(self):
		change_request = create_change_request(self.project, self.customer, "_Test board draft change")

		row = board_row(self.project, change_request.name)
		self.assertEqual(row.actions, [{"action": "Approve", "next_state": "Approved"}])
		self.assertEqual(row.realization_assignee, "Administrator")
		self.assertTrue(row.realization_assignee_name)
		self.assertTrue(row.state_changed_on)
		self.assertIsNone(row.task_status)

	def test_approving_moves_to_task_created_and_reports_the_task(self):
		change_request = create_change_request(self.project, self.customer, "_Test board approve")
		frappe.db.set_value(
			"Change Request", change_request.name, "state_changed_on", OLD_TIMESTAMP, update_modified=False
		)

		result = apply_change_request_action(change_request.name, "Approve")

		self.assertEqual(result["workflow_state"], "Task Created")
		self.assertTrue(result["task"])
		row = board_row(self.project, change_request.name)
		self.assertEqual(row.task, result["task"])
		self.assertEqual(row.task_status, "Open")
		self.assertGreater(get_datetime(row.state_changed_on), get_datetime(OLD_TIMESTAMP))
		self.assertEqual([action["action"] for action in row.actions], ["Cancel"])

		task = frappe.get_doc("Task", result["task"])
		task.status = "Completed"
		task.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Change Request", change_request.name, "workflow_state"), "Done")

		task.status = "Open"
		task.save(ignore_permissions=True)
		self.assertEqual(
			frappe.db.get_value("Change Request", change_request.name, "workflow_state"), "Task Created"
		)

	def test_action_outside_the_workflow_is_refused(self):
		change_request = create_change_request(self.project, self.customer, "_Test board refused")

		with self.assertRaises(frappe.ValidationError):
			apply_change_request_action(change_request.name, "Mark Done")

	def test_backfill_dates_task_created_from_the_task(self):
		approved = create_change_request(self.project, self.customer, "_Test backfill approved")
		apply_change_request_action(approved.name, "Approve")
		draft = create_change_request(self.project, self.customer, "_Test backfill draft")
		for name in (approved.name, draft.name):
			frappe.db.set_value("Change Request", name, "state_changed_on", None, update_modified=False)

		backfill_change_request_state_changed_on.execute()

		task = frappe.db.get_value("Change Request", approved.name, "task")
		self.assertEqual(
			get_datetime(frappe.db.get_value("Change Request", approved.name, "state_changed_on")),
			get_datetime(frappe.db.get_value("Task", task, "creation")),
		)
		self.assertEqual(
			get_datetime(frappe.db.get_value("Change Request", draft.name, "state_changed_on")),
			get_datetime(frappe.db.get_value("Change Request", draft.name, "creation")),
		)
