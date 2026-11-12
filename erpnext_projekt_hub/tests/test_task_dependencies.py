import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.api.project_hub import get_project_tasks

test_ignore = ["Task"]


class TestTaskDependencies(FrappeTestCase):
	"""get_project_tasks exposes Task Depends On rows as `depends_on` for the timeline arrows."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.project = frappe.get_doc(
			{
				"doctype": "Project",
				"project_name": "_Test Timeline Dependencies",
				"status": "Open",
				"company": frappe.db.get_value("Company", {}, "name"),
			}
		).insert(ignore_permissions=True)

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
