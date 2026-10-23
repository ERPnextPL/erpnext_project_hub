from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import get_datetime

from erpnext_projekt_hub.api.project_hub import (
	_set_change_request_tasks,
	apply_customer_request_action,
	create_change_request_from_customer_request,
	get_project_requests,
	update_customer_request_analysis,
)
from erpnext_projekt_hub.patches.post_model_sync import backfill_customer_request_state_changed_on
from erpnext_projekt_hub.projekt_hub.doctype.customer_request.test_customer_request import (
	create_project,
	get_or_create_customer,
)
from erpnext_projekt_hub.projekt_hub.doctype.customer_request.test_customer_request_analysis_queue import (
	create_request_to_analyze,
)

test_ignore = ["Customer", "Project", "Quotation", "Task"]

OLD_TIMESTAMP = "2026-01-01 08:00:00"


def create_request(project, customer, subject, **values):
	return frappe.get_doc(
		{
			"doctype": "Customer Request",
			"customer": customer,
			"project": project,
			"subject": subject,
			**values,
		}
	).insert(ignore_permissions=True)


def add_version(name, changed):
	return frappe.get_doc(
		{
			"doctype": "Version",
			"ref_doctype": "Customer Request",
			"docname": name,
			"data": frappe.as_json({"changed": changed}),
		}
	).insert(ignore_permissions=True)


def board_row(project, name):
	return next(row for row in get_project_requests(project)["customer_requests"] if row.name == name)


class TestCustomerRequestsBoard(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.customer = get_or_create_customer()
		self.project = create_project(self.customer)

	def test_state_changed_on_moves_only_with_the_workflow_state(self):
		customer_request = create_request(self.project, self.customer, "_Test state since")
		self.assertTrue(customer_request.state_changed_on)

		frappe.db.set_value(
			"Customer Request",
			customer_request.name,
			"state_changed_on",
			OLD_TIMESTAMP,
			update_modified=False,
		)
		customer_request.reload()
		customer_request.subject = "_Test state since, renamed"
		customer_request.save()
		self.assertEqual(get_datetime(customer_request.state_changed_on), get_datetime(OLD_TIMESTAMP))

		apply_customer_request_action(customer_request.name, "Submit for Analysis")
		state_changed_on = frappe.db.get_value("Customer Request", customer_request.name, "state_changed_on")
		self.assertGreater(get_datetime(state_changed_on), get_datetime(OLD_TIMESTAMP))

	def test_conversion_moves_state_changed_on(self):
		customer_request = create_request(
			self.project, self.customer, "_Test converted state since", analysis="_Test analysis"
		)
		frappe.db.set_value(
			"Customer Request",
			customer_request.name,
			{"workflow_state": "Accepted", "state_changed_on": OLD_TIMESTAMP},
			update_modified=False,
		)

		create_change_request_from_customer_request(customer_request.name)

		state_changed_on = frappe.db.get_value("Customer Request", customer_request.name, "state_changed_on")
		self.assertGreater(get_datetime(state_changed_on), get_datetime(OLD_TIMESTAMP))

	def test_board_rows_carry_analysis_and_edit_access(self):
		draft = create_request(self.project, self.customer, "_Test board draft")
		waiting = create_request_to_analyze(self.project, self.customer, "_Test board analysis")
		frappe.db.set_value(
			"Customer Request", waiting.name, "analysis", "<p>_Test written</p>", update_modified=False
		)

		draft_row = board_row(self.project, draft.name)
		waiting_row = board_row(self.project, waiting.name)

		self.assertFalse(draft_row.can_edit_analysis)
		self.assertTrue(waiting_row.can_edit_analysis)
		self.assertEqual(waiting_row.analysis, "<p>_Test written</p>")
		self.assertIn("state_changed_on", waiting_row)

	def test_update_analysis_saves_estimate_of_request_waiting_for_analysis(self):
		customer_request = create_request_to_analyze(self.project, self.customer, "_Test save analysis")

		update_customer_request_analysis(
			customer_request.name,
			analysis="<p>_Test analysis</p>",
			estimated_hours="6.5",
			currency="PLN",
			estimated_amount="1300",
		)

		values = frappe.db.get_value(
			"Customer Request",
			customer_request.name,
			["analysis", "estimated_hours", "currency", "estimated_amount", "workflow_state"],
			as_dict=True,
		)
		self.assertEqual(values.analysis, "<p>_Test analysis</p>")
		self.assertEqual(values.estimated_hours, 6.5)
		self.assertEqual(values.currency, "PLN")
		self.assertEqual(values.estimated_amount, 1300)
		self.assertEqual(values.workflow_state, "To Analyze")

		# The saved analysis is what marking the request quoted needs.
		apply_customer_request_action(customer_request.name, "Mark Quoted")
		self.assertEqual(
			frappe.db.get_value("Customer Request", customer_request.name, "workflow_state"), "Quoted"
		)

	def test_update_analysis_keeps_fields_left_out_and_clears_empty_ones(self):
		customer_request = create_request_to_analyze(self.project, self.customer, "_Test partial analysis")
		update_customer_request_analysis(
			customer_request.name, analysis="<p>_Test first</p>", estimated_hours="3"
		)

		update_customer_request_analysis(customer_request.name, estimated_hours="")

		values = frappe.db.get_value(
			"Customer Request", customer_request.name, ["analysis", "estimated_hours"], as_dict=True
		)
		self.assertEqual(values.analysis, "<p>_Test first</p>")
		self.assertEqual(values.estimated_hours, 0)

	def test_update_analysis_is_refused_outside_analysis(self):
		customer_request = create_request(self.project, self.customer, "_Test draft analysis")

		with self.assertRaises(frappe.PermissionError):
			update_customer_request_analysis(customer_request.name, analysis="<p>_Test</p>")

	def test_update_analysis_rejects_negative_estimate_and_amount_without_currency(self):
		customer_request = create_request_to_analyze(self.project, self.customer, "_Test invalid estimate")

		with self.assertRaises(frappe.ValidationError):
			update_customer_request_analysis(customer_request.name, estimated_hours="-1")
		with self.assertRaises(frappe.ValidationError):
			update_customer_request_analysis(customer_request.name, estimated_amount="100", currency="")

	def test_update_analysis_rejects_non_numeric_estimates(self):
		customer_request = create_request_to_analyze(
			self.project, self.customer, "_Test non numeric estimate"
		)

		with self.assertRaises(frappe.ValidationError):
			update_customer_request_analysis(customer_request.name, estimated_hours="abc")
		with self.assertRaises(frappe.ValidationError):
			update_customer_request_analysis(customer_request.name, estimated_amount="not-a-number")

	def test_change_request_tasks_read_ignores_task_permissions(self):
		row = frappe._dict(task="_Test linked task")
		task = frappe._dict(name="_Test linked task", subject="_Test subject", status="Working", progress=25)

		with patch("erpnext_projekt_hub.api.project_hub.frappe.get_all", return_value=[task]) as get_all:
			_set_change_request_tasks([row])

		get_all.assert_called_once_with(
			"Task",
			filters={"name": ["in", ["_Test linked task"]]},
			fields=["name", "subject", "status", "progress"],
			ignore_permissions=True,
		)
		self.assertEqual(row.task_status, "Working")

	def test_backfill_takes_last_state_change_from_version_log(self):
		moved = create_request(self.project, self.customer, "_Test backfill moved")
		never_moved = create_request(self.project, self.customer, "_Test backfill new")
		# Documents skip the version log under tests, so write the entries here:
		# a state change, then a later edit that must not count as one.
		state_change = add_version(moved.name, [["workflow_state", "Draft", "To Analyze"]])
		add_version(moved.name, [["subject", "_Test backfill moved", "_Test backfill renamed"]])
		for name in (moved.name, never_moved.name):
			frappe.db.set_value("Customer Request", name, "state_changed_on", None, update_modified=False)

		backfill_customer_request_state_changed_on.execute()

		self.assertEqual(
			get_datetime(frappe.db.get_value("Customer Request", moved.name, "state_changed_on")),
			get_datetime(state_change.creation),
		)
		self.assertEqual(
			get_datetime(frappe.db.get_value("Customer Request", never_moved.name, "state_changed_on")),
			get_datetime(frappe.db.get_value("Customer Request", never_moved.name, "creation")),
		)
