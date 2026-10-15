import frappe

OLD = "is_overdue"
NEW = "hub_is_overdue"


def execute():
	"""Rename the Hub's Task custom field ``is_overdue`` to ``hub_is_overdue``.

	ERPNext now defines a ``Task.is_overdue`` property, so a custom field with that
	name is rejected as conflicting with a meta object and breaks fixtures sync.
	Runs before model sync so the column and the Custom Field record move together
	and the fixture then finds the renamed field instead of creating a second one.
	"""
	old_name, new_name = f"Task-{OLD}", f"Task-{NEW}"
	if not frappe.db.exists("Custom Field", old_name):
		return

	column_exists = frappe.db.has_column("Task", OLD)
	if frappe.db.exists("Custom Field", new_name):
		# Fixture already created the new field; carry the data over and drop the old one.
		if column_exists and frappe.db.has_column("Task", NEW):
			frappe.db.sql(f"update `tabTask` set `{NEW}` = `{OLD}`")
		frappe.db.delete("Custom Field", {"name": old_name})
	else:
		frappe.db.set_value("Custom Field", old_name, {"fieldname": NEW}, update_modified=False)
		frappe.rename_doc("Custom Field", old_name, new_name, force=True)

	if column_exists:
		if frappe.db.has_column("Task", NEW):
			frappe.db.sql_ddl(f"alter table `tabTask` drop column `{OLD}`")
		else:
			frappe.db.sql_ddl(f"alter table `tabTask` rename column `{OLD}` to `{NEW}`")

	frappe.clear_cache(doctype="Task")
