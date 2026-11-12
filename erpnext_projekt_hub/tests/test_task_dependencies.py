import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.api.project_hub import get_project_tasks

test_ignore = ["Task"]


class TestTaskDependencies(FrappeTestCase):
	"""get_project_tasks exposes Task Depends On rows as `depends_on` for the timeline arrows."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		# Project names are unique: create the project once for the whole class.
		existing = frappe.db.get_value("Project", {"project_name": "_Test Timeline Dependencies"})
		cls.project = (
			frappe.get_doc("Project", existing)
			if existing
			else frappe.get_doc(
				{
					"doctype": "Project",
					"project_name": "_Test Timeline Dependencies",
					"status": "Open",
					"company": frappe.db.get_value("Company", {}, "name"),
				}
			).insert(ignore_permissions=True)
		)

	def setUp(self):
		frappe.set_user("Administrator")

	def _task(self, subject, depends_on=None):
		return frappe.get_doc(
			{
				"doctype": "Task",
				"subject": subject,
				"project": self.project.name,
				"depends_on": [{"task": name} for name in (depends_on or [])],
			}
		).insert(ignore_permissions=True)

	def _tasks_by_name(self):
		result = get_project_tasks(self.project.name, apply_default_status_filter=0)
		return {task["name"]: task for task in result["tasks"]}

	def test_task_without_dependencies_has_empty_list(self):
		task = self._task("_Test Dep - alone")
		self.assertEqual(self._tasks_by_name()[task.name]["depends_on"], [])

	def test_depends_on_lists_predecessors(self):
		first = self._task("_Test Dep - first")
		second = self._task("_Test Dep - second")
		third = self._task("_Test Dep - third", depends_on=[first.name, second.name])

		tasks = self._tasks_by_name()
		self.assertCountEqual(tasks[third.name]["depends_on"], [first.name, second.name])
		self.assertEqual(tasks[first.name]["depends_on"], [])
		self.assertEqual(tasks[second.name]["depends_on"], [])


class TestReorderTaskParent(FrappeTestCase):
	"""Attaching / detaching a task to a parent through reorder_task."""

	def setUp(self):
		frappe.set_user("Administrator")

	def _task(self, subject, parent=None, is_group=0):
		# ERPNext only accepts a parent that is a group task.
		return frappe.get_doc(
			{"doctype": "Task", "subject": subject, "parent_task": parent, "is_group": is_group}
		).insert(ignore_permissions=True)

	def test_attach_and_detach(self):
		from erpnext_projekt_hub.api.project_hub import reorder_task

		parent = self._task("_Test Parent - parent")
		child = self._task("_Test Parent - child")

		reorder_task(child.name, parent.name, 0)
		self.assertEqual(frappe.db.get_value("Task", child.name, "parent_task"), parent.name)
		self.assertEqual(frappe.db.get_value("Task", parent.name, "is_group"), 1)

		reorder_task(child.name, None, 0)
		self.assertFalse(frappe.db.get_value("Task", child.name, "parent_task"))

	def test_cannot_move_under_own_descendant(self):
		from erpnext_projekt_hub.api.project_hub import reorder_task

		root = self._task("_Test Parent - root", is_group=1)
		mid = self._task("_Test Parent - mid", parent=root.name, is_group=1)
		leaf = self._task("_Test Parent - leaf", parent=mid.name)

		with self.assertRaises(frappe.ValidationError):
			reorder_task(root.name, leaf.name, 0)
		with self.assertRaises(frappe.ValidationError):
			reorder_task(root.name, root.name, 0)
		self.assertFalse(frappe.db.get_value("Task", root.name, "parent_task"))


class TestSubtaskCounts(FrappeTestCase):
	"""The board card of a parent task shows done/total subtasks."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_task_response_has_subtask_counts(self):
		from erpnext_projekt_hub.api.project_hub import _get_task_response

		parent = frappe.get_doc(
			{"doctype": "Task", "subject": "_Test Count - parent", "is_group": 1}
		).insert(ignore_permissions=True)
		for subject, status in (("a", "Completed"), ("b", "Open"), ("c", "Completed")):
			frappe.get_doc(
				{
					"doctype": "Task",
					"subject": f"_Test Count - {subject}",
					"parent_task": parent.name,
					"status": status,
				}
			).insert(ignore_permissions=True)

		response = _get_task_response(frappe.get_doc("Task", parent.name))
		self.assertEqual(response["subtask_count"], 3)
		self.assertEqual(response["subtask_done"], 2)
