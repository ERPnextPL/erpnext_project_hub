import frappe

DEFAULT_DESCRIPTIONS = (
	"Poprawa poprawki",
	"Analiza błędu",
	"Programowanie",
	"Spotkanie",
	"Kontakt z klientem",
)


def execute():
	for idx, description in enumerate(DEFAULT_DESCRIPTIONS):
		if frappe.db.exists("Quick Time Log Description", description):
			continue
		frappe.get_doc(
			{
				"doctype": "Quick Time Log Description",
				"description": description,
				"sort_order": idx,
			}
		).insert(ignore_permissions=True)
