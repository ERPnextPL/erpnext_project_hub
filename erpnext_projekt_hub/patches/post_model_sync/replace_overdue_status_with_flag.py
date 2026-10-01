from __future__ import annotations

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import getdate, today

FALLBACK_STATUS = "Open"


def execute():
	"""Move tasks off the "Overdue" status onto the ``is_overdue`` flag.

	From now on HubTask.update_status() only sets the flag, but tasks already
	switched by ERPNext's daily job still carry "Overdue" as their status. The
	job writes it with db_set, so no Version records that step; the last status
	a person set is still in the history though, and that is what gets restored.
	Fixtures sync after post_model_sync patches, so the field is created here.
	"""
	create_custom_fields(
		{
			"Task": [
				{
					"fieldname": "is_overdue",
					"fieldtype": "Check",
					"label": "Overdue",
					"insert_after": "status",
					"default": "0",
					"read_only": 1,
					"no_copy": 1,
					"in_standard_filter": 1,
				}
			]
		},
		update=False,
	)

	statuses = _status_lookup()
	for name in frappe.get_all("Task", filters={"status": "Overdue"}, pluck="name"):
		frappe.db.set_value(
			"Task", name, "status", _last_status_before_overdue(name, statuses), update_modified=False
		)

	today_date = getdate(today())
	tasks = frappe.get_all(
		"Task",
		filters={"status": ["not in", ["Completed", "Cancelled", "Template"]], "exp_end_date": ["is", "set"]},
		fields=["name", "exp_end_date"],
	)
	overdue = [t.name for t in tasks if getdate(t.exp_end_date) < today_date]
	if overdue:
		frappe.db.set_value("Task", {"name": ["in", overdue]}, "is_overdue", 1, update_modified=False)


def _status_lookup():
	"""Map stored and displayed status values to the stored one.

	Version records keep the value as it was displayed to the person saving,
	so a Polish user leaves "W trakcie" in the history instead of "Working".
	"""
	options = [o for o in frappe.get_meta("Task").get_options("status").split("\n") if o]
	lookup = {}
	languages = {"en", frappe.db.get_default("lang") or "en"}
	languages.update(
		frappe.get_all("User", filters={"language": ["is", "set"]}, pluck="language", distinct=True)
	)
	current_lang = frappe.local.lang
	try:
		for lang in languages:
			frappe.local.lang = lang
			for option in options:
				lookup[frappe._(option)] = option
	finally:
		frappe.local.lang = current_lang
	lookup.update({option: option for option in options})
	return lookup


def _last_status_before_overdue(task_name, statuses):
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Task", "docname": task_name},
		fields=["data"],
		order_by="creation desc",
	)
	for version in versions:
		try:
			changed = json.loads(version.data or "{}").get("changed") or []
		except ValueError:
			continue
		for field, _old, new in changed:
			status = statuses.get(new) if field == "status" else None
			if status and status not in ("Overdue", "Template"):
				return status
	return FALLBACK_STATUS
