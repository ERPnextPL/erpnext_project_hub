import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.api.project_hub import create_timelog, get_task_timelogs, update_timelog

test_ignore = ["Task", "Timesheet"]


def create_task(subject):
	return frappe.get_doc({"doctype": "Task", "subject": subject}).insert(ignore_permissions=True)


def get_log(task_name, timelog_name):
	logs = get_task_timelogs(task_name)["timelogs"]
	return next(log for log in logs if log.timelog_name == timelog_name)


class TestTaskTimelogEdit(FrappeTestCase):
	"""Task Detail lets the author edit a time log only while its timesheet is a draft."""

	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("Activity Type", "_Test Timelog Edit"):
			frappe.get_doc({"doctype": "Activity Type", "activity_type": "_Test Timelog Edit"}).insert(
				ignore_permissions=True
			)
		self.task = create_task("_Test Timelog Edit")
		self.log = create_timelog(
			task=self.task.name,
			hours=1,
			activity_type="_Test Timelog Edit",
			description="Initial entry",
			from_time="2026-10-01 08:00:00",
			to_time="2026-10-01 09:00:00",
		)

	def test_own_draft_entry_is_editable(self):
		log = get_log(self.task.name, self.log["timelog_name"])
		self.assertEqual(log.docstatus, 0)
		self.assertEqual(log.can_edit, 1)

	def test_update_draft_entry(self):
		update_timelog(
			self.log["timelog_name"],
			hours=2.5,
			description="Corrected entry",
			from_time="2026-10-01 08:00:00",
			to_time="2026-10-01 10:30:00",
		)

		log = get_log(self.task.name, self.log["timelog_name"])
		self.assertEqual(log.hours, 2.5)
		self.assertEqual(log.description, "Corrected entry")

	def test_submitted_entry_is_locked(self):
		frappe.get_doc("Timesheet", self.log["timesheet_name"]).submit()

		log = get_log(self.task.name, self.log["timelog_name"])
		self.assertEqual(log.can_edit, 0)
		with self.assertRaises(frappe.ValidationError):
			update_timelog(self.log["timelog_name"], hours=3)

	def test_other_users_entry_is_not_editable(self):
		frappe.set_user("Guest")
		log = get_log(self.task.name, self.log["timelog_name"])
		self.assertEqual(log.can_edit, 0)
