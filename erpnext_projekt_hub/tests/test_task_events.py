import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.api.project_hub import delete_task

test_ignore = ["Task"]


def create_task(subject, status="Open", parent=None, is_group=0):
	return frappe.get_doc(
		{
			"doctype": "Task",
			"subject": subject,
			"status": status,
			"parent_task": parent,
			"is_group": is_group,
		}
	).insert(ignore_permissions=True)


def set_status(task, status):
	task.reload()
	task.status = status
	task.save(ignore_permissions=True)
	return task


class TestSubtaskDoesNotDriveParentStatus(FrappeTestCase):
	"""A subtask change must leave the parent's status alone."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_completing_subtask_leaves_open_parent_open(self):
		parent = create_task("_Test Parent - stays open", is_group=1)
		sub = create_task("_Test Sub - completed", parent=parent.name)

		set_status(sub, "Completed")

		parent.reload()
		self.assertEqual(parent.status, "Open")

	def test_completing_subtask_leaves_working_parent_working(self):
		parent = create_task("_Test Parent - stays working", status="Working", is_group=1)
		sub = create_task("_Test Sub - completed too", parent=parent.name)

		set_status(sub, "Completed")

		parent.reload()
		self.assertEqual(parent.status, "Working")

	def test_all_subtasks_completed_does_not_auto_complete_parent(self):
		parent = create_task("_Test Parent - no auto complete", status="Working", is_group=1)
		first = create_task("_Test Sub A", parent=parent.name)
		second = create_task("_Test Sub B", parent=parent.name)

		set_status(first, "Completed")
		set_status(second, "Completed")

		parent.reload()
		self.assertEqual(parent.status, "Working")
		self.assertEqual(parent.progress, 100)

	def test_starting_subtask_leaves_open_parent_open(self):
		parent = create_task("_Test Parent - subtask started", is_group=1)
		sub = create_task("_Test Sub - started", parent=parent.name)

		set_status(sub, "Working")

		parent.reload()
		self.assertEqual(parent.status, "Open")


class TestParentProgressRollup(FrappeTestCase):
	"""Progress still rolls up even though status does not."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_progress_reflects_completed_subtasks(self):
		parent = create_task("_Test Parent - progress", is_group=1)
		first = create_task("_Test Progress Sub A", parent=parent.name)
		create_task("_Test Progress Sub B", parent=parent.name)

		set_status(first, "Completed")

		parent.reload()
		self.assertEqual(parent.progress, 50)

	def test_cancelled_subtasks_drop_out_of_the_total(self):
		parent = create_task("_Test Parent - cancelled sub", is_group=1)
		done = create_task("_Test Cancelled Sub A", parent=parent.name)
		cancelled = create_task("_Test Cancelled Sub B", parent=parent.name)

		set_status(done, "Completed")
		set_status(cancelled, "Cancelled")

		parent.reload()
		self.assertEqual(parent.progress, 100)

	def test_leaf_task_keeps_manual_progress(self):
		leaf = create_task("_Test Leaf - manual progress")
		leaf.progress = 42
		leaf.save(ignore_permissions=True)

		leaf.reload()
		self.assertEqual(leaf.progress, 42)

	def test_deleting_subtask_recalculates_parent_progress(self):
		parent = create_task("_Test Parent - deleted subtask", is_group=1)
		completed = create_task("_Test Deleted Subtask", parent=parent.name)
		create_task("_Test Remaining Subtask", parent=parent.name)

		set_status(completed, "Completed")
		parent.reload()
		self.assertEqual(parent.progress, 50)

		delete_task(completed.name)

		parent.reload()
		self.assertEqual(parent.progress, 0)


class TestCompletedParentIsUncompleted(FrappeTestCase):
	"""The one exception: a Completed parent cannot hold unfinished work."""

	def setUp(self):
		frappe.set_user("Administrator")

	def _completed_parent_with_completed_subtask(self, label):
		parent = create_task(f"_Test Parent - {label}", is_group=1)
		sub = create_task(f"_Test Sub - {label}", parent=parent.name)
		set_status(sub, "Completed")
		set_status(parent, "Completed")
		return parent, sub

	def test_reopening_subtask_takes_parent_off_completed(self):
		parent, sub = self._completed_parent_with_completed_subtask("reopen")

		set_status(sub, "Working")

		parent.reload()
		self.assertEqual(parent.status, "Working")

	def test_subtask_back_to_open_takes_parent_off_completed(self):
		parent, sub = self._completed_parent_with_completed_subtask("back to open")

		set_status(sub, "Open")

		parent.reload()
		self.assertEqual(parent.status, "Working")

	def test_subtask_in_review_takes_parent_off_completed(self):
		parent, sub = self._completed_parent_with_completed_subtask("review")

		set_status(sub, "Pending Review")

		parent.reload()
		self.assertEqual(parent.status, "Working")

	def test_new_subtask_takes_parent_off_completed(self):
		parent = create_task("_Test Parent - gains subtask", status="Completed", is_group=1)

		create_task("_Test Sub - newly added", parent=parent.name)

		parent.reload()
		self.assertEqual(parent.status, "Working")

	def test_cancelling_subtask_leaves_parent_completed(self):
		parent, sub = self._completed_parent_with_completed_subtask("cancel")

		set_status(sub, "Cancelled")

		parent.reload()
		self.assertEqual(parent.status, "Completed")

	def test_reopen_propagates_to_completed_grandparent(self):
		grandparent = create_task("_Test Grandparent", is_group=1)
		parent = create_task("_Test Middle", parent=grandparent.name, is_group=1)
		sub = create_task("_Test Deep Sub", parent=parent.name)

		set_status(sub, "Completed")
		set_status(parent, "Completed")
		set_status(grandparent, "Completed")

		set_status(sub, "Working")

		parent.reload()
		grandparent.reload()
		self.assertEqual(parent.status, "Working")
		self.assertEqual(grandparent.status, "Working")

	def test_reopen_propagates_past_an_already_working_parent(self):
		"""A Completed ancestor further up the chain must still be reopened
		even when the nearer ancestor in between is already off Completed."""
		grandparent = create_task("_Test Grandparent - past working parent", is_group=1)
		parent = create_task("_Test Middle - already working", parent=grandparent.name, is_group=1)
		sub = create_task("_Test Deep Sub - reopened", parent=parent.name)

		set_status(sub, "Completed")
		set_status(parent, "Completed")
		set_status(grandparent, "Completed")

		# Parent already left Completed independently of this walk (e.g. a
		# stale import), while grandparent is still Completed.
		frappe.db.set_value("Task", parent.name, "status", "Working", update_modified=False)

		set_status(sub, "Working")

		parent.reload()
		grandparent.reload()
		self.assertEqual(parent.status, "Working")
		self.assertEqual(grandparent.status, "Working")

	def test_reopen_stops_at_an_ancestor_that_was_not_completed(self):
		grandparent = create_task("_Test Grandparent - open", status="Open", is_group=1)
		parent = create_task("_Test Middle - open", parent=grandparent.name, is_group=1)
		sub = create_task("_Test Deep Sub - open branch", parent=parent.name)

		set_status(sub, "Completed")
		set_status(sub, "Working")

		grandparent.reload()
		self.assertEqual(grandparent.status, "Open")


class TestDependenciesDoNotDriveStatus(FrappeTestCase):
	"""The Depends On table no longer moves any status."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_reopening_a_dependency_leaves_the_task_completed(self):
		dependency = create_task("_Test Dependency", status="Completed")
		dependent = create_task("_Test Dependent")
		dependent.append("depends_on", {"task": dependency.name})
		dependent.save(ignore_permissions=True)

		set_status(dependent, "Completed")
		set_status(dependency, "Working")

		dependent.reload()
		self.assertEqual(dependent.status, "Completed")

	def test_completing_all_dependencies_does_not_complete_the_task(self):
		dependency = create_task("_Test Dependency - pending")
		dependent = create_task("_Test Dependent - stays open")
		dependent.append("depends_on", {"task": dependency.name})
		dependent.save(ignore_permissions=True)

		set_status(dependency, "Completed")

		dependent.reload()
		self.assertEqual(dependent.status, "Open")
