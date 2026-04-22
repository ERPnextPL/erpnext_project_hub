import frappe
from frappe import _
from frappe.installer import update_site_config


def before_install():
	"""
	Ensure erpnext is installed before installing Projekt HUB.
	"""
	installed_apps = frappe.get_installed_apps()
	if "erpnext" not in installed_apps:
		frappe.throw(_("The erpnext app is required to install Projekt HUB. Please install erpnext first."))


def after_install():
	"""Mark the PRO frontend as enabled for the installed site."""
	update_site_config("projekt_hub_pro_enabled", 1)
