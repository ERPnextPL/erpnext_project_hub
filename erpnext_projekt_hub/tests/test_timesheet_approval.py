from unittest.mock import patch

import frappe
from frappe.model.workflow import WorkflowTransitionError, apply_workflow
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub import timesheet_approval as approval
from erpnext_projekt_hub.access import PROJEKT_HUB_ROLE
from erpnext_projekt_hub.api.project_hub import (
	create_timelog,
	get_my_timelogs,
	get_task_timelogs,
	send_timelog_for_approval,
	send_timesheets_for_approval,
	update_timelog,
	withdraw_timesheets_from_approval,
)

test_ignore = ["Task", "Timesheet", "Project"]

EMPLOYEE = "_test_ts_employee@example.com"
APPROVER = "_test_ts_approver@example.com"  # Projects Manager
MANAGER = "_test_ts_manager@example.com"  # Timesheet Manager
PROJECT_MANAGER = "_test_ts_project_manager@example.com"  # Project Manager (kierownik projektu)
SYSADMIN = "_test_ts_sysadmin@example.com"  # System Manager only
SENDMAIL = "erpnext_projekt_hub.timesheet_approval.frappe.sendmail"
HAS_EMAIL_ACCOUNT = "erpnext_projekt_hub.timesheet_approval._has_outgoing_email_account"


def ensure_user(email, first_name, *roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": first_name, "send_welcome_email": 0}
		).insert()
	frappe.get_doc("User", email).add_roles(PROJEKT_HUB_ROLE, *roles)


def act(user, timesheet_name, action):
	frappe.set_user(user)
	return apply_workflow(frappe.get_doc("Timesheet", timesheet_name), action)


def recipients_of(sendmail):
	return [user for call in sendmail.call_args_list for user in call.kwargs["recipients"]]


class TestTimesheetApproval(FrappeTestCase):
	"""Draft -> Pending Approval -> Approved / Rejected, with the server-side guards."""

	def setUp(self):
		frappe.set_user("Administrator")
		approval.setup()
		ensure_user(EMPLOYEE, "Employee", "Projects User")
		ensure_user(APPROVER, "Approver", "Projects Manager")
		ensure_user(MANAGER, "Manager", approval.TIMESHEET_MANAGER)
		ensure_user(PROJECT_MANAGER, "Project Lead", approval.PROJECT_MANAGER)
		ensure_user(SYSADMIN, "Admin", "System Manager")
		if not frappe.db.exists("Activity Type", "_Test Approval"):
			frappe.get_doc({"doctype": "Activity Type", "activity_type": "_Test Approval"}).insert()

		# The project manager is who gets asked to approve the project's hours.
		project = frappe.new_doc("Project")
		project.project_name = "_Test Timesheet Approval"
		project.company = frappe.db.get_value("Company", {}, "name")
		project.project_manager = APPROVER
		project.insert()
		self.task = frappe.get_doc(
			{"doctype": "Task", "subject": "_Test Approval", "project": project.name}
		).insert()

		frappe.set_user(EMPLOYEE)
		self.log = self.log_hours("2026-10-05 08:00:00", "2026-10-05 10:00:00")
		self.timesheet = self.log["timesheet_name"]

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def log_hours(self, from_time, to_time):
		return create_timelog(
			task=self.task.name,
			hours=2,
			activity_type="_Test Approval",
			description="Work",
			from_time=from_time,
			to_time=to_time,
		)

	def state(self):
		return frappe.db.get_value(
			"Timesheet", self.timesheet, ["workflow_state", "docstatus", "status"], as_dict=True
		)

	def send_and_reject(self, reason="Wrong project"):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		frappe.set_user(APPROVER)
		approval.reject_timesheet(self.timesheet, reason)

	def test_new_timesheet_starts_as_draft(self):
		self.assertEqual(self.state().workflow_state, approval.DRAFT)
		self.assertEqual(self.state().docstatus, 0)

	def test_approval_submits_and_keeps_billing_status(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		self.assertEqual(self.state().workflow_state, approval.PENDING)
		self.assertTrue(frappe.db.get_value("Timesheet", self.timesheet, "approval_requested_on"))

		act(APPROVER, self.timesheet, approval.APPROVE)

		state = self.state()
		self.assertEqual((state.workflow_state, state.docstatus), (approval.APPROVED, 1))
		# status keeps tracking billing
		self.assertEqual(state.status, "Submitted")
		self.assertEqual(frappe.db.get_value("Timesheet", self.timesheet, "reviewed_by"), APPROVER)

	def test_employee_cannot_approve(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		with self.assertRaises(WorkflowTransitionError):
			act(EMPLOYEE, self.timesheet, approval.APPROVE)

	def test_reject_requires_reason(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		frappe.set_user(APPROVER)
		with self.assertRaises(frappe.ValidationError):
			apply_workflow(frappe.get_doc("Timesheet", self.timesheet), approval.REJECT)
		with self.assertRaises(frappe.ValidationError):
			approval.reject_timesheet(self.timesheet, "   ")
		self.assertEqual(self.state().workflow_state, approval.PENDING)

	def test_rejection_stores_reason_and_employee_resubmits(self):
		self.send_and_reject("Hours belong to another project")

		doc = frappe.get_doc("Timesheet", self.timesheet)
		self.assertEqual(doc.workflow_state, approval.REJECTED)
		self.assertEqual(doc.rejection_reason, "Hours belong to another project")
		self.assertEqual(doc.reviewed_by, APPROVER)
		self.assertTrue(
			frappe.db.exists(
				"Comment",
				{
					"reference_doctype": "Timesheet",
					"reference_name": self.timesheet,
					"comment_type": "Comment",
					"content": ["like", "%Hours belong to another project%"],
				},
			)
		)

		# the employee corrects the hours and sends them again
		frappe.set_user(EMPLOYEE)
		update_timelog(self.log["timelog_name"], hours=1.5, to_time="2026-10-05 09:30:00")
		act(EMPLOYEE, self.timesheet, approval.RESUBMIT)

		doc.reload()
		self.assertEqual(doc.workflow_state, approval.PENDING)
		self.assertFalse(doc.rejection_reason)
		self.assertFalse(doc.reviewed_by)

	def test_pending_timesheet_is_locked_for_employee(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)

		frappe.set_user(EMPLOYEE)
		log = next(
			log
			for log in get_task_timelogs(self.task.name)["timelogs"]
			if log.timelog_name == self.log["timelog_name"]
		)
		self.assertEqual(log.can_edit, 0)
		with self.assertRaises(frappe.ValidationError):
			update_timelog(self.log["timelog_name"], hours=3)

		doc = frappe.get_doc("Timesheet", self.timesheet)
		doc.time_logs[0].description = "Changed while waiting"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

		# the approver may still correct it
		frappe.set_user(APPROVER)
		doc = frappe.get_doc("Timesheet", self.timesheet)
		doc.time_logs[0].description = "Corrected by approver"
		doc.save()

	def test_plain_submit_is_blocked(self):
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc("Timesheet", self.timesheet).submit()

		# not even with the state set by hand: Draft -> Approved is no transition
		doc = frappe.get_doc("Timesheet", self.timesheet)
		doc.workflow_state = approval.APPROVED
		with self.assertRaises(frappe.ValidationError):
			doc.submit()
		self.assertEqual(self.state().docstatus, 0)

	def test_only_timesheet_manager_cancels(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		act(APPROVER, self.timesheet, approval.APPROVE)

		frappe.set_user(APPROVER)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("Timesheet", self.timesheet).cancel()

		act(MANAGER, self.timesheet, approval.CANCEL)
		state = self.state()
		self.assertEqual((state.workflow_state, state.docstatus), (approval.CANCELLED, 2))

	def test_new_hours_do_not_join_a_pending_timesheet(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)

		frappe.set_user(EMPLOYEE)
		log = self.log_hours(frappe.utils.now(), frappe.utils.now())

		self.assertNotEqual(log["timesheet_name"], self.timesheet)
		self.assertEqual(
			frappe.db.get_value("Timesheet", log["timesheet_name"], "workflow_state"), approval.DRAFT
		)

	def test_send_for_approval_from_project_hub(self):
		self.send_and_reject()
		frappe.set_user(EMPLOYEE)
		draft = self.log_hours(frappe.utils.now(), frappe.utils.now())["timesheet_name"]

		result = send_timesheets_for_approval([self.timesheet, draft])

		self.assertEqual(sorted(result["sent"]), sorted([self.timesheet, draft]))
		self.assertEqual(result["failed"], [])
		for name in (self.timesheet, draft):
			self.assertEqual(frappe.db.get_value("Timesheet", name, "workflow_state"), approval.PENDING)

		# already waiting: reported back, nothing raised
		again = send_timesheets_for_approval([draft])
		self.assertEqual(again["sent"], [])
		self.assertEqual(again["failed"][0]["timesheet"], draft)

	def test_send_one_time_log_from_a_shared_timesheet(self):
		timesheet = frappe.get_doc("Timesheet", self.timesheet)
		timesheet.append(
			"time_logs",
			{
				"activity_type": "_Test Approval",
				"hours": 1,
				"from_time": "2026-10-05 10:00:00",
				"to_time": "2026-10-05 11:00:00",
				"task": self.task.name,
				"project": self.task.project,
			},
		)
		timesheet.save()
		second_log_name = timesheet.time_logs[-1].name

		frappe.set_user(EMPLOYEE)
		result = send_timelog_for_approval(self.log["timelog_name"])

		self.assertEqual(result["timelog"], self.log["timelog_name"])
		self.assertEqual(
			frappe.db.get_value("Timesheet", result["sent"][0], "workflow_state"),
			approval.PENDING,
		)
		self.assertEqual(
			frappe.db.get_value("Timesheet Detail", self.log["timelog_name"], "parent"),
			result["sent"][0],
		)
		self.assertEqual(
			frappe.db.get_value("Timesheet", self.timesheet, "workflow_state"),
			approval.DRAFT,
		)
		self.assertEqual(
			frappe.db.get_value("Timesheet Detail", second_log_name, "parent"),
			self.timesheet,
		)

	def test_cannot_send_someone_elses_timesheet(self):
		frappe.set_user(APPROVER)
		result = send_timesheets_for_approval([self.timesheet])
		self.assertEqual(result["sent"], [])
		self.assertEqual(self.state().workflow_state, approval.DRAFT)

	def test_my_time_status_filters(self):
		self.send_and_reject()
		frappe.set_user(EMPLOYEE)
		pending = self.log_hours(frappe.utils.now(), frappe.utils.now())["timesheet_name"]
		act(EMPLOYEE, pending, approval.SEND_FOR_APPROVAL)
		frappe.set_user(EMPLOYEE)

		def timesheets(status):
			return {log.timesheet_name for log in get_my_timelogs(status=status)["timelogs"]}

		self.assertIn(self.timesheet, timesheets("To Send"))
		self.assertIn(self.timesheet, timesheets("Rejected"))
		self.assertNotIn(pending, timesheets("To Send"))
		self.assertEqual(timesheets("Pending Approval"), {pending})
		rejected_log = get_my_timelogs(status="Rejected")["timelogs"][0]
		self.assertEqual(rejected_log.rejection_reason, "Wrong project")
		self.assertEqual(rejected_log.reviewed_by_name, "Approver")

	@patch(HAS_EMAIL_ACCOUNT, return_value=True)
	def test_notifications(self, _has_email_account):
		with patch(SENDMAIL) as sendmail:
			act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		# the project manager is asked, not the employee who sent it
		self.assertEqual(recipients_of(sendmail), [APPROVER])

		with patch(SENDMAIL) as sendmail:
			frappe.set_user(APPROVER)
			approval.reject_timesheet(self.timesheet, "Missing description")
		self.assertEqual(recipients_of(sendmail), [EMPLOYEE])
		self.assertIn("Missing description", sendmail.call_args.kwargs["message"])
		self.assertTrue(
			frappe.db.exists(
				"Notification Log",
				{"for_user": EMPLOYEE, "document_type": "Timesheet", "document_name": self.timesheet},
			)
		)

		with patch(SENDMAIL) as sendmail:
			act(EMPLOYEE, self.timesheet, approval.RESUBMIT)
			act(APPROVER, self.timesheet, approval.APPROVE)
		self.assertEqual(recipients_of(sendmail), [APPROVER, EMPLOYEE])

	@patch(HAS_EMAIL_ACCOUNT, return_value=False)
	def test_without_email_account_the_bell_still_rings(self, _has_email_account):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		frappe.set_user(APPROVER)
		frappe.clear_messages()
		with patch(SENDMAIL, side_effect=AssertionError("no e-mail without an account")) as sendmail:
			approval.reject_timesheet(self.timesheet, "Missing description")

		sendmail.assert_not_called()
		self.assertEqual(frappe.get_message_log(), [])
		self.assertTrue(
			frappe.db.exists(
				"Notification Log",
				{"for_user": EMPLOYEE, "document_type": "Timesheet", "document_name": self.timesheet},
			)
		)

	def test_failing_notification_does_not_block_or_show_errors(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		frappe.set_user(APPROVER)
		frappe.clear_messages()

		def broken(*args, **kwargs):
			frappe.throw("Mail server down")

		with patch(HAS_EMAIL_ACCOUNT, return_value=True), patch(SENDMAIL, side_effect=broken):
			apply_workflow(frappe.get_doc("Timesheet", self.timesheet), approval.APPROVE)

		self.assertEqual(self.state().workflow_state, approval.APPROVED)
		self.assertEqual(frappe.get_message_log(), [])

	def test_approvers_fall_back_to_timesheet_managers(self):
		doc = frappe.get_doc("Timesheet", self.timesheet)
		for row in doc.time_logs:
			row.project = None
		doc.parent_project = None
		self.assertIn(MANAGER, approval.get_approvers(doc))
		self.assertNotIn(EMPLOYEE, approval.get_approvers(doc))

	def test_backfill_of_existing_timesheets(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		act(APPROVER, self.timesheet, approval.APPROVE)
		frappe.set_user(EMPLOYEE)
		draft = self.log_hours(frappe.utils.now(), frappe.utils.now())["timesheet_name"]
		for name in (self.timesheet, draft):
			frappe.db.set_value("Timesheet", name, "workflow_state", None, update_modified=False)

		approval.backfill_workflow_state()

		self.assertEqual(self.state().workflow_state, approval.APPROVED)
		self.assertEqual(frappe.db.get_value("Timesheet", draft, "workflow_state"), approval.DRAFT)

	# Withdraw
	# --------

	def test_author_withdraws_before_review_and_can_correct(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)

		act(EMPLOYEE, self.timesheet, approval.WITHDRAW)

		doc = frappe.get_doc("Timesheet", self.timesheet)
		self.assertEqual((doc.workflow_state, doc.docstatus), (approval.DRAFT, 0))
		self.assertFalse(doc.approval_requested_on)
		frappe.set_user(EMPLOYEE)
		update_timelog(self.log["timelog_name"], hours=1, to_time="2026-10-05 09:00:00")
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		self.assertEqual(self.state().workflow_state, approval.PENDING)

	def test_only_the_author_can_withdraw(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		for user in (APPROVER, SYSADMIN):
			with self.assertRaises(WorkflowTransitionError, msg=user):
				act(user, self.timesheet, approval.WITHDRAW)
		self.assertEqual(self.state().workflow_state, approval.PENDING)

	def test_withdraw_from_project_hub(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		frappe.set_user(EMPLOYEE)

		result = withdraw_timesheets_from_approval([self.timesheet])

		self.assertEqual(result, {"withdrawn": [self.timesheet], "failed": []})
		self.assertEqual(self.state().workflow_state, approval.DRAFT)
		# a draft cannot be withdrawn again
		again = withdraw_timesheets_from_approval([self.timesheet])
		self.assertEqual(again["withdrawn"], [])
		self.assertEqual(again["failed"][0]["timesheet"], self.timesheet)

	def test_reviewed_timesheet_cannot_be_withdrawn(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		act(APPROVER, self.timesheet, approval.APPROVE)
		with self.assertRaises(WorkflowTransitionError):
			act(EMPLOYEE, self.timesheet, approval.WITHDRAW)

	# No self-approval
	# ----------------

	def log_own_hours(self, user):
		frappe.set_user(user)
		name = self.log_hours("2026-10-06 08:00:00", "2026-10-06 10:00:00")["timesheet_name"]
		act(user, name, approval.SEND_FOR_APPROVAL)
		return name

	def test_approver_cannot_approve_or_reject_own_hours(self):
		own = self.log_own_hours(APPROVER)

		frappe.set_user(APPROVER)
		with self.assertRaises(frappe.ValidationError):
			apply_workflow(frappe.get_doc("Timesheet", own), approval.APPROVE)
		with self.assertRaises(frappe.PermissionError):
			approval.reject_timesheet(own, "Not mine to judge")
		self.assertEqual(frappe.db.get_value("Timesheet", own, "workflow_state"), approval.PENDING)

		# another approver reviews them
		act(MANAGER, own, approval.APPROVE)
		self.assertEqual(frappe.db.get_value("Timesheet", own, "workflow_state"), approval.APPROVED)

	def test_hours_entered_for_the_approver_by_someone_else_are_still_theirs(self):
		frappe.set_user("Administrator")
		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Approver",
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
				"company": frappe.db.get_value("Company", {}, "name"),
				"user_id": APPROVER,
			}
		).insert()
		doc = frappe.get_doc(
			{
				"doctype": "Timesheet",
				"employee": employee.name,
				"time_logs": [
					{
						"activity_type": "_Test Approval",
						"hours": 1,
						"from_time": "2026-10-07 08:00:00",
						"to_time": "2026-10-07 09:00:00",
					}
				],
			}
		).insert()
		apply_workflow(doc, approval.SEND_FOR_APPROVAL)

		with self.assertRaises(frappe.PermissionError):
			act(APPROVER, doc.name, approval.APPROVE)

	def test_approver_cannot_edit_own_pending_hours(self):
		own = self.log_own_hours(APPROVER)
		frappe.set_user(APPROVER)
		doc = frappe.get_doc("Timesheet", own)
		doc.time_logs[0].description = "Changed after sending"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_project_manager_role_approves(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)
		act(PROJECT_MANAGER, self.timesheet, approval.APPROVE)
		self.assertEqual(self.state().workflow_state, approval.APPROVED)

	# System Manager: full rights
	# ---------------------------

	def test_system_manager_sees_approves_and_cancels(self):
		act(EMPLOYEE, self.timesheet, approval.SEND_FOR_APPROVAL)

		frappe.set_user(SYSADMIN)
		self.assertIn(self.timesheet, frappe.get_list("Timesheet", pluck="name"))
		act(SYSADMIN, self.timesheet, approval.APPROVE)
		act(SYSADMIN, self.timesheet, approval.CANCEL)
		self.assertEqual(self.state().workflow_state, approval.CANCELLED)

	def test_system_manager_approves_own_hours(self):
		own = self.log_own_hours(SYSADMIN)
		act(SYSADMIN, own, approval.APPROVE)
		self.assertEqual(frappe.db.get_value("Timesheet", own, "workflow_state"), approval.APPROVED)

	def test_submit_permission_comes_from_the_workflow(self):
		def can_submit(role):
			return frappe.db.get_value(
				"Custom DocPerm", {"parent": "Timesheet", "role": role, "permlevel": 0}, "submit"
			)

		for role in ("Projects User", "HR User"):
			self.assertFalse(can_submit(role), role)
		for role in (
			"Projects Manager",
			approval.PROJECT_MANAGER,
			approval.TIMESHEET_MANAGER,
			"System Manager",
		):
			self.assertTrue(can_submit(role), role)
