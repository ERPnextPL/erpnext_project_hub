import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.api.project_hub import quick_update_task, update_task

test_ignore = ["Task"]


def create_task(subject, status="Open"):
	return frappe.get_doc({"doctype": "Task", "subject": subject, "status": status}).insert(
		ignore_permissions=True
	)


class TestBlockedFlag(FrappeTestCase):
	"""The blocked flag is switched by hand from both task views and keeps the status."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_new_task_is_not_blocked(self):
		task = create_task("_Test Blocked - new")
		self.assertEqual(task.is_blocked, 0)

	def test_update_task_sets_and_clears_flag(self):
		task = create_task("_Test Blocked - outliner", status="Working")

		response = update_task(task.name, is_blocked="1")
		self.assertEqual(response["is_blocked"], 1)
		self.assertEqual(frappe.db.get_value("Task", task.name, "is_blocked"), 1)
		self.assertEqual(response["status"], "Working")

		response = update_task(task.name, is_blocked=0)
		self.assertEqual(response["is_blocked"], 0)
		self.assertEqual(frappe.db.get_value("Task", task.name, "is_blocked"), 0)

	def test_quick_update_sets_and_clears_flag(self):
		task = create_task("_Test Blocked - my tasks", status="Pending Review")

		response = quick_update_task(task.name, is_blocked=1)
		self.assertEqual(response["is_blocked"], 1)
		self.assertEqual(response["status"], "Pending Review")

		response = quick_update_task(task.name, is_blocked="0")
		self.assertEqual(response["is_blocked"], 0)

	def test_quick_update_without_flag_keeps_it(self):
		task = create_task("_Test Blocked - untouched")
		quick_update_task(task.name, is_blocked=1)

		response = quick_update_task(task.name, priority="High")
		self.assertEqual(response["is_blocked"], 1)
