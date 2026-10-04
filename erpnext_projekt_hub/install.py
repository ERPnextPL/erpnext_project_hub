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


def before_tests():
	_ensure_test_roots()


def after_install():
	"""Mark the PRO frontend as enabled for the installed site."""
	_ensure_test_roots()
	_ensure_project_custom_fields()
	update_site_config("projekt_hub_pro_enabled", 1)


def _ensure_project_custom_fields():
	# Patches are skipped on fresh installs, so create the fields here as well.
	from erpnext_projekt_hub.patches.post_model_sync.ensure_project_manager_field import execute

	execute()


def _ensure_test_roots():
	for doctype, name, fieldname in [
		("Item Group", "All Item Groups", "item_group_name"),
		("Warehouse Type", "Transit", None),
		("Territory", "All Territories", "territory_name"),
		("Customer Group", "All Customer Groups", "customer_group_name"),
		("Supplier Group", "All Supplier Groups", "supplier_group_name"),
		("Sales Person", "Sales Team", "sales_person_name"),
	]:
		if frappe.db.exists(doctype, name):
			continue

		doc = frappe.get_doc({"doctype": doctype, "name": name})
		if fieldname:
			doc.set(fieldname, name)
		if doctype in ("Item Group", "Territory", "Customer Group", "Supplier Group", "Sales Person"):
			doc.is_group = 1
		doc.insert(ignore_permissions=True)
