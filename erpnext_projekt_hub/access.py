import frappe

ALLOWED_ROLES = {"Project Manager", "Projects User", "System Manager"}


def has_project_hub_access(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return False
	if user == "Administrator":
		return True
	return bool(set(frappe.get_roles(user)) & ALLOWED_ROLES)
