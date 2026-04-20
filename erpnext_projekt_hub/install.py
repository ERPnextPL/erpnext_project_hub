from pathlib import Path

import frappe
from frappe import _

PRO_ENABLED_MARKER = Path(__file__).resolve().parents[1] / "frontend" / ".pro-enabled"


def before_install():
	"""
	Ensure erpnext is installed before installing Projekt HUB.
	"""
	installed_apps = frappe.get_installed_apps()
	if "erpnext" not in installed_apps:
		frappe.throw(_("The erpnext app is required to install Projekt HUB. Please install erpnext first."))


def after_install():
	"""Mark the PRO frontend as enabled for the installed site."""
	PRO_ENABLED_MARKER.write_text("enabled\n", encoding="utf-8")
