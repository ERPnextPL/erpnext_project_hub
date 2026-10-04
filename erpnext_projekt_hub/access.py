import frappe
from frappe import _

# Holders of this role open Projekt HUB and are the only users offered for task and
# project assignment and @mentions. System Manager keeps access so admins cannot lock
# themselves out.
PROJEKT_HUB_ROLE = "Projekt HUB User"
ALLOWED_ROLES = {PROJEKT_HUB_ROLE, "System Manager"}

# Roles that plan the work of the whole team. Everybody else with Hub access plans
# only the days of their own Employee record (see api.work_planning).
PLANNER_ROLES = {"Project Manager", "Projects Manager", "System Manager"}


def has_project_hub_access(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return False
	if user == "Administrator":
		return True
	return bool(set(frappe.get_roles(user)) & ALLOWED_ROLES)


def require_project_hub_access():
	"""Throw PermissionError unless the session user may use Projekt HUB."""
	if not has_project_hub_access():
		frappe.throw(_("You do not have permission to access Projekt HUB"), frappe.PermissionError)


def ensure_projekt_hub_role():
	"""Create the role that grants access to Projekt HUB, if missing."""
	if frappe.db.exists("Role", PROJEKT_HUB_ROLE):
		return

	frappe.get_doc({"doctype": "Role", "role_name": PROJEKT_HUB_ROLE, "desk_access": 1}).insert(
		ignore_permissions=True
	)


def get_projekt_hub_user_names() -> list[str]:
	"""Return the users holding the Projekt HUB role."""
	return frappe.get_all(
		"Has Role",
		filters={"role": PROJEKT_HUB_ROLE, "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)


def can_plan_for_others(user: str | None = None) -> bool:
	"""Return True when the user may plan the work of employees other than themselves."""
	user = user or frappe.session.user
	if user == "Guest":
		return False
	if user == "Administrator":
		return True
	return bool(set(frappe.get_roles(user)) & PLANNER_ROLES)


def get_own_employee(user: str | None = None) -> str | None:
	"""Return the active Employee record linked to the user, if there is one."""
	user = user or frappe.session.user
	if user in ("Guest", "Administrator"):
		return None
	return frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
