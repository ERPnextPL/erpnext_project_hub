import frappe

ALLOWED_ROLES = {"Project Manager", "Projects User", "System Manager"}

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
