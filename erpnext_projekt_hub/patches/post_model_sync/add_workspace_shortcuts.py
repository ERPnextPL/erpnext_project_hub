import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import generate_hash

WORKSPACE_NAME = "Projects"
APP_NAME = "erpnext_projekt_hub"

SHORTCUTS = [
	{
		"type": "DocType",
		"link_to": "Project Milestone",
		"label": "Project Milestone",
		"color": "Purple",
		"doc_view": "List",
	},
	{
		"type": "URL",
		"link_to": "/project-hub",
		"label": "Projekt HUB",
		"color": "Blue",
	},
]


CUSTOM_FIELDS = {
	"Task": [
		{
			"fieldname": "milestone",
			"fieldtype": "Link",
			"label": "Milestone",
			"options": "Project Milestone",
			"insert_after": "is_milestone",
			"in_standard_filter": 1,
			"description": "Link to Project Milestone",
		}
	],
	"Project": [
		{
			"fieldname": "project_manager",
			"fieldtype": "Link",
			"label": "Project Manager",
			"options": "User",
			"insert_after": "department",
			"description": "User responsible for project management",
		},
		{
			"fieldname": "documentation_url",
			"fieldtype": "Data",
			"label": "Documentation URL",
			"options": "URL",
			"insert_after": "project_manager",
			"description": "Link to project documentation",
		},
	],
	"Projects Settings": [
		{
			"fieldname": "default_activity_type",
			"fieldtype": "Link",
			"label": "Default Activity Type",
			"options": "Activity Type",
			"insert_after": "fetch_timesheet_in_sales_invoice",
			"description": "Global default activity type for all projects",
		}
	],
}


def execute():
	if APP_NAME not in frappe.get_installed_apps():
		return

	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)

	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = False

	for shortcut in SHORTCUTS:
		if _ensure_shortcut(workspace, shortcut):
			changed = True

	content, content_changed = _ensure_shortcuts_in_content(workspace.content)
	if content_changed:
		workspace.content = content
		changed = True

	if changed:
		workspace.flags.ignore_links = True
		workspace.save(ignore_permissions=True)


def _ensure_shortcut(workspace, shortcut):
	link_to = shortcut["link_to"]
	label = shortcut["label"]

	existing = next(
		(r for r in workspace.shortcuts if r.link_to == link_to or r.label == label),
		None,
	)

	if existing:
		updated = False
		for field, value in shortcut.items():
			if getattr(existing, field, None) != value:
				setattr(existing, field, value)
				updated = True
		return updated

	workspace.append("shortcuts", shortcut)
	return True


def _ensure_shortcuts_in_content(raw_content):
	try:
		content = json.loads(raw_content) if raw_content else []
	except json.JSONDecodeError:
		content = []

	existing_names = {
		entry.get("data", {}).get("shortcut_name") for entry in content if entry.get("type") == "shortcut"
	}

	missing = [s["label"] for s in SHORTCUTS if s["label"] not in existing_names]

	if not missing:
		return json.dumps(content), False

	insert_at = len(content)
	in_shortcut_section = False

	for idx, entry in enumerate(content):
		if entry.get("type") == "header":
			text = (entry.get("data") or {}).get("text", "")
			if "Your Shortcuts" in text:
				in_shortcut_section = True
			continue

		if in_shortcut_section and entry.get("type") != "shortcut":
			insert_at = idx
			break

	for label in missing:
		block = {
			"id": generate_hash(length=10),
			"type": "shortcut",
			"data": {"shortcut_name": label, "col": 3},
		}
		content.insert(insert_at, block)
		insert_at += 1

	return json.dumps(content), True
