from frappe.installer import update_site_config


def after_uninstall():
	"""Disable the PRO frontend for the uninstalled site."""
	update_site_config("projekt_hub_pro_enabled", 0)
