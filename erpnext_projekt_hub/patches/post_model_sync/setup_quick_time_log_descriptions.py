import frappe

DEFAULT_DESCRIPTIONS = (
	("Poprawa poprawki", "Wykonanie"),
	("Analiza błędu", "Wykonanie"),
	("Programowanie", "Wykonanie"),
	("Spotkanie", "Komunikacja"),
	("Kontakt z klientem", "Komunikacja"),
)


def execute():
	for idx, (description, activity_type) in enumerate(DEFAULT_DESCRIPTIONS):
		activity_type_exists = frappe.db.exists("Activity Type", activity_type)
		existing_name = frappe.db.get_value("Quick Time Log Description", {"description": description})

		if not existing_name:
			frappe.get_doc(
				{
					"doctype": "Quick Time Log Description",
					"description": description,
					"activity_type": activity_type if activity_type_exists else None,
					"sort_order": idx,
				}
			).insert(ignore_permissions=True)
			continue

		# Backfill activity_type on records created before this field existed,
		# without overwriting a value an admin may have already set.
		if activity_type_exists and not frappe.db.get_value(
			"Quick Time Log Description", existing_name, "activity_type"
		):
			frappe.db.set_value("Quick Time Log Description", existing_name, "activity_type", activity_type)
