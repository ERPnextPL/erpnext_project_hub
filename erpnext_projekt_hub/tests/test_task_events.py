import frappe
from frappe.tests.utils import FrappeTestCase

test_ignore = ["Task"]


def create_task(subject, status="Open"):
	return frappe.get_doc(
		{
			"doctype": "Task",
			"subject": subject,
			"status": status,
		}
	).insert(ignore_permissions=True)


class TestSyncProgressFromDependencies(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_without_dependencies_is_noop(self):
		parent = create_task("_Test Parent - no deps")
		parent.progress = 42
		parent.save(ignore_permissions=True)

		self.assertEqual(parent.progress, 42)

	def test_partial_completion_computes_percent(self):
		done = create_task("_Test Dep Done", status="Completed")
		open_task = create_task("_Test Dep Open", status="Open")
		parent = create_task("_Test Parent - partial")
		parent.append("depends_on", {"task": done.name})
		parent.append("depends_on", {"task": open_task.name})
		parent.save(ignore_permissions=True)

		self.assertEqual(parent.progress, 50)
		self.assertNotEqual(parent.status, "Completed")

	def test_cancelled_dependency_excluded_from_total(self):
		done = create_task("_Test Dep Done - cancelled case", status="Completed")
		cancelled = create_task("_Test Dep Cancelled", status="Cancelled")
		parent = create_task("_Test Parent - cancelled dep")
		parent.append("depends_on", {"task": done.name})
		parent.append("depends_on", {"task": cancelled.name})
		parent.save(ignore_permissions=True)

		# effective_total excludes the cancelled dependency, so 1/1 = 100%
		self.assertEqual(parent.progress, 100)
		self.assertEqual(parent.status, "Completed")

	def test_all_completed_auto_completes_status(self):
		done_one = create_task("_Test Dep Done 1", status="Completed")
		done_two = create_task("_Test Dep Done 2", status="Completed")
		parent = create_task("_Test Parent - all done")
		parent.append("depends_on", {"task": done_one.name})
		parent.append("depends_on", {"task": done_two.name})
		parent.save(ignore_permissions=True)

		self.assertEqual(parent.progress, 100)
		self.assertEqual(parent.status, "Completed")
