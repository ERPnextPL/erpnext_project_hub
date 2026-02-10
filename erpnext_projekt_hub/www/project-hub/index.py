"""
Project Outliner page controller.
"""

import frappe
from frappe import _
from frappe.website.utils import get_boot_data

no_cache = 1


def get_context(context):
	"""Set up context for the outliner page."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access Project Outliner"), frappe.PermissionError)

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True

	# Pass CSRF token and boot data to template
	context.csrf_token = frappe.session.csrf_token
	context.boot = get_boot_data()

	return context
