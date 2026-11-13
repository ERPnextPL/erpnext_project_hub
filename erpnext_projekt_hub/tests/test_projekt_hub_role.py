import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.access import PROJEKT_HUB_ROLE, ensure_projekt_hub_role, has_project_hub_access
from erpnext_projekt_hub.api import project_hub

HUB_USER = "_test_projekt_hub_member@example.com"
OTHER_USER = "_test_projekt_hub_outsider@example.com"
SYSTEM_MANAGER = "_test_projekt_hub_sysmanager@example.com"


class TestProjektHubRole(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_projekt_hub_role()
		self.make_user(HUB_USER, "Projects User", PROJEKT_HUB_ROLE)
		self.make_user(OTHER_USER, "Projects User")
		self.make_user(SYSTEM_MANAGER, "System Manager")

	def tearDown(self):
		frappe.set_user("Administrator")

	@staticmethod
	def make_user(email, *roles):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": email.split("@")[0],
					"send_welcome_email": 0,
				}
			).insert()
		user = frappe.get_doc("User", email)
		user.add_roles(*roles)

	def test_only_role_holders_get_hub_access(self):
		self.assertTrue(has_project_hub_access(HUB_USER))
		self.assertFalse(has_project_hub_access(OTHER_USER))
		self.assertTrue(has_project_hub_access("Administrator"))
		self.assertFalse(has_project_hub_access("Guest"))

	def test_assignable_users_are_role_holders(self):
		names = {user.name for user in project_hub.get_users()}
		self.assertIn(HUB_USER, names)
		self.assertNotIn(OTHER_USER, names)

	def test_mentionable_users_are_role_holders(self):
		frappe.cache.delete_value("users_for_mentions")
		ids = {option["id"] for option in project_hub.get_mention_options()}
		self.assertIn(HUB_USER, ids)
		self.assertNotIn(OTHER_USER, ids)

	def test_hub_api_rejects_users_without_the_role(self):
		frappe.set_user(OTHER_USER)
		with self.assertRaises(frappe.PermissionError):
			project_hub.get_users()

		frappe.set_user(HUB_USER)
		project_hub.get_users()

	def test_task_completion_assignees_follow_task_permission(self):
		# The Desk Task form asks for assignees when any Task editor completes a
		# task, so this endpoint must not require the Projekt HUB role.
		task = frappe.get_doc({"doctype": "Task", "subject": "_Test completion assignees"}).insert()
		frappe.set_user(OTHER_USER)
		self.assertEqual(project_hub.get_task_completion_assignees(task.name), [])

	def test_system_manager_can_create_users(self):
		# Test users are created without ignore_permissions, so the fixtures (and
		# real admins) rely on System Manager being allowed to create users.
		frappe.set_user(SYSTEM_MANAGER)
		email = f"_test_projekt_hub_{frappe.generate_hash(length=8)}@example.com"
		self.make_user(email, "Projects User")
		self.assertTrue(frappe.db.exists("User", email))
