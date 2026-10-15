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
	old_field_exists = frappe.db.exists("Custom Field", old_name)
	column_exists = frappe.db.has_column("Task", OLD)
	if not (old_field_exists or column_exists):
		return

	# Column first: DDL commits implicitly, so a failure here leaves the Custom Field
	# untouched and the patch is picked up again on the next run.
	if column_exists:
		if frappe.db.has_column("Task", NEW):
			# sync_all already added the new column; carry over what is still unset.
			task = frappe.qb.DocType("Task")
			frappe.qb.update(task).set(task[NEW], task[OLD]).where(task[NEW] == 0).run()
			frappe.db.sql_ddl(f"alter table `tabTask` drop column `{OLD}`")
		else:
			frappe.db.sql_ddl(f"alter table `tabTask` rename column `{OLD}` to `{NEW}`")

	if old_field_exists:
		if frappe.db.exists("Custom Field", new_name):
			# Fixture already created the new field.
			frappe.db.delete("Custom Field", {"name": old_name})
		else:
			frappe.db.set_value("Custom Field", old_name, {"fieldname": NEW}, update_modified=False)
			frappe.rename_doc("Custom Field", old_name, new_name, force=True)

	frappe.clear_cache(doctype="Task")
