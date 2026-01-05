import frappe


def check_milestone_field():
	"""Check if milestone custom field exists on Task"""
	# Check if Custom Field exists
	exists = frappe.db.exists("Custom Field", "Task-milestone")
	print(f"Custom Field 'Task-milestone' exists: {exists}")

	# Check Task table columns
	columns = frappe.db.sql("SHOW COLUMNS FROM `tabTask` LIKE 'milestone'", as_dict=True)
	print(f"Column 'milestone' in tabTask: {len(columns) > 0}")
	if columns:
		print(f"Column details: {columns[0]}")

	return exists
