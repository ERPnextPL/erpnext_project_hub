import frappe
from frappe import _


def before_install():
	"""
	Ensure erpnext is installed before installing Projekt HUB.
	"""
	installed_apps = frappe.get_installed_apps()
	if "erpnext" not in installed_apps:
		frappe.throw(_("The erpnext app is required to install Projekt HUB. Please install erpnext first."))


def after_install():
	"""Placeholder hook for any post-install setup the app requires."""
	pass
