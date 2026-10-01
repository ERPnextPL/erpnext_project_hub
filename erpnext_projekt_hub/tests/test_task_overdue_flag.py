import frappe
from erpnext.projects.doctype.task.task import set_tasks_as_overdue
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

test_ignore = ["Task"]


def create_task(subject, status="Open", exp_end_date=None):
	return frappe.get_doc(
		{
			"doctype": "Task",
			"subject": subject,
			"status": status,
			"exp_end_date": exp_end_date,
		}
	).insert(ignore_permissions=True)


class TestOverdueFlag(FrappeTestCase):
	"""A missed due date sets a flag and never replaces the task's status."""

	def setUp(self):
		frappe.set_user("Administrator")

	def _make_past_due(self, task):
		# Insert validation would refuse nothing here, but a direct write mimics
		# a task whose due date simply passed overnight with the flag still unset.
		frappe.db.set_value(
			"Task", task.name, {"exp_end_date": add_days(today(), -3), "is_overdue": 0}, update_modified=False
		)

	def test_scheduler_keeps_pending_review_and_sets_flag(self):
		task = create_task(
			"_Test Overdue - in review", status="Pending Review", exp_end_date=add_days(today(), 5)
		)
		self._make_past_due(task)

		set_tasks_as_overdue()

		task.reload()
		self.assertEqual(task.status, "Pending Review")
		self.assertEqual(task.is_overdue, 1)

	def test_scheduler_leaves_completed_task_unflagged(self):
		task = create_task("_Test Overdue - completed", status="Completed", exp_end_date=add_days(today(), 5))
		self._make_past_due(task)

		set_tasks_as_overdue()

		task.reload()
		self.assertEqual(task.status, "Completed")
		self.assertEqual(task.is_overdue, 0)

	def test_moving_due_date_to_future_clears_flag(self):
		task = create_task(
			"_Test Overdue - rescheduled", status="Working", exp_end_date=add_days(today(), -2)
		)
		self.assertEqual(task.is_overdue, 1)

		task.exp_end_date = add_days(today(), 4)
		task.save(ignore_permissions=True)

		self.assertEqual(task.is_overdue, 0)
		self.assertEqual(task.status, "Working")

	def test_completing_task_clears_flag(self):
		task = create_task(
			"_Test Overdue - finished late", status="Working", exp_end_date=add_days(today(), -2)
		)

		task.status = "Completed"
		task.save(ignore_permissions=True)

		self.assertEqual(task.is_overdue, 0)
