"""
Test milestone compatibility between erpnext_projekt_hub and project_control.

Ensures both apps maintain synchronized logic for Project Milestone calculations.
Tests use code inspection to avoid Frappe framework dependencies.

Run with: bench run-tests --app erpnext_projekt_hub
"""

import unittest
import inspect


class TestHubMilestoneLogicSync(unittest.TestCase):
	"""Validate that hub's milestone logic uses correct patterns"""

	def test_completed_status_not_closed(self):
		"""Project Milestone must use 'Completed' status, not 'Closed'"""
		from erpnext_projekt_hub.projekt_hub.doctype.project_milestone.project_milestone import ProjectMilestone

		# Get source code of update_statistics method
		source = inspect.getsource(ProjectMilestone.update_statistics)

		# Should NOT contain old "Closed" status
		self.assertNotIn('"Closed"', source, "Found 'Closed' status - must use 'Completed'")
		self.assertNotIn("'Closed'", source, "Found 'Closed' status - must use 'Completed'")

		# Should contain "Completed" status
		self.assertIn("Completed", source, "Must check for 'Completed' status")

	def test_uses_db_count_not_get_list(self):
		"""Should use efficient frappe.db.count() not frappe.get_list()"""
		from erpnext_projekt_hub.projekt_hub.doctype.project_milestone.project_milestone import ProjectMilestone

		source = inspect.getsource(ProjectMilestone.update_statistics)

		# Should use db.count
		self.assertIn("frappe.db.count", source, "Must use frappe.db.count for efficiency")

	def test_get_health_status_method(self):
		"""Test get_health_status method is available"""
		from erpnext_projekt_hub.projekt_hub.doctype.project_milestone.project_milestone import ProjectMilestone

		# Should have get_health_status method
		self.assertTrue(hasattr(ProjectMilestone, 'get_health_status'))

		source = inspect.getsource(ProjectMilestone.get_health_status)

		# Should have health status logic
		self.assertIn("overdue", source)
		self.assertIn("at_risk", source)
		self.assertIn("on_track", source)

	def test_auto_advance_logic_exists(self):
		"""Verify auto-advance logic exists in update_statistics"""
		from erpnext_projekt_hub.projekt_hub.doctype.project_milestone.project_milestone import ProjectMilestone

		source = inspect.getsource(ProjectMilestone.update_statistics)

		# Should have auto-advance logic
		self.assertIn("In Progress", source, "Should have In Progress status")
		self.assertIn("progress", source.lower(), "Should check progress")

	def test_task_events_have_correct_logic(self):
		"""Verify task_events has auto-advance logic"""
		from erpnext_projekt_hub.events import task_events

		source = inspect.getsource(task_events.update_milestone_progress)

		# Should check for "Completed" status
		self.assertIn("Completed", source)

		# Should have auto-advance logic
		self.assertIn("In Progress", source)
		self.assertIn("progress", source.lower())

	def test_doctype_exists(self):
		"""Verify Project Milestone doctype is properly defined"""
		from erpnext_projekt_hub.projekt_hub.doctype.project_milestone.project_milestone import ProjectMilestone

		# Should have required methods
		required_methods = ['validate', 'on_trash', 'get_health_status', 'update_statistics']
		for method_name in required_methods:
			self.assertTrue(
				hasattr(ProjectMilestone, method_name),
				f"Missing required method: {method_name}"
			)


if __name__ == '__main__':
	unittest.main()
