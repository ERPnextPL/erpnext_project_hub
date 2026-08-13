from __future__ import annotations

import frappe
from frappe.utils import cint


def execute():
	"""Enable Track Changes on Task so status transitions land in Version history.

	ERPNext ships Task without ``track_changes``, so ``Document.save_version()``
	returns early on every save and no Version record is ever written. The task
	timeline therefore shows no status history at all, which makes it impossible
	to tell who or what moved a task from Completed back to Working.

	Task belongs to ERPNext, so the flag is set through a Property Setter rather
	than by editing the shipped DocType JSON.
	"""
	existing = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "Task", "property": "track_changes"},
		["name", "value"],
		as_dict=True,
	)

	if existing:
		if cint(existing.value) != 1:
			frappe.db.set_value("Property Setter", existing.name, "value", 1)
			frappe.clear_cache(doctype="Task")
		return

	frappe.make_property_setter(
		{
			"doctype": "Task",
			"doctype_or_field": "DocType",
			"property": "track_changes",
			"value": 1,
			"property_type": "Check",
		}
	)
