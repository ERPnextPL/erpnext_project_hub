"""
Project Outliner page controller.
"""

import frappe
from frappe import _
from frappe.website.utils import get_boot_data

no_cache = 1


ALLOWED_ROLES = {"Project Manager", "Projects User", "System Manager"}


def get_context(context):
	"""Set up context for the outliner page."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access Project Outliner"), frappe.PermissionError)

	if frappe.session.user != "Administrator":
		user_roles = set(frappe.get_roles(frappe.session.user))
		if not user_roles & ALLOWED_ROLES:
			frappe.throw(_("You do not have permission to access Projekt HUB"), frappe.PermissionError)

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True

	# Pass CSRF token and boot data to template
	context.csrf_token = frappe.session.csrf_token
	context.boot = get_boot_data()

	return context
