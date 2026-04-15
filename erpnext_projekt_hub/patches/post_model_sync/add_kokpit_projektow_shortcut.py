import json

import frappe
from frappe.utils import generate_hash

WORKSPACE_NAME = "Projects"
ERPNEXT_APP = "erpnext"
PROJECT_CONTROL_APP = "project_control"
PAGE_NAME = "kokpit-projektow"
SHORTCUT_LABEL = "Kokpit Projektów"
SHORTCUT_URL = f"/app/{PAGE_NAME}"


def execute():
	if ERPNEXT_APP not in frappe.get_installed_apps():
		return

	if PROJECT_CONTROL_APP not in frappe.get_installed_apps():
		return

	if not frappe.db.exists("Page", PAGE_NAME):
		return

	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = ensure_workspace_shortcut(workspace)

	content, content_changed = ensure_shortcut_in_content(workspace.content)
	if content_changed:
		workspace.content = content
		changed = True

	if changed:
		workspace.flags.ignore_links = True
		workspace.save(ignore_permissions=True)


def ensure_workspace_shortcut(workspace):
	shortcuts = getattr(workspace, "shortcuts", []) or []
	existing = next(
		(row for row in shortcuts if row.type == "URL" and row.link_to == SHORTCUT_URL),
		None,
	)

	if existing:
		changed = False
		if existing.label != SHORTCUT_LABEL:
			existing.label = SHORTCUT_LABEL
			changed = True
		if existing.color != "Green":
			existing.color = "Green"
			changed = True
		return changed

	workspace.append(
		"shortcuts",
		{
			"type": "URL",
			"link_to": SHORTCUT_URL,
			"label": SHORTCUT_LABEL,
			"color": "Green",
		},
	)
	return True


def ensure_shortcut_in_content(raw_content):
	if not raw_content:
		content = []
	else:
		try:
			content = json.loads(raw_content)
		except json.JSONDecodeError:
			return raw_content, False

	found = False
	insert_at = len(content)
	visible_shortcut_area = False

	for idx, entry in enumerate(content):
		if entry.get("type") == "shortcut":
			name = entry.get("data", {}).get("shortcut_name")
			if name == SHORTCUT_LABEL:
				found = True
				break
			continue

		if entry.get("type") == "header":
			text = (entry.get("data") or {}).get("text", "")
			if "Your Shortcuts" in text:
				visible_shortcut_area = True
			continue

		if visible_shortcut_area and entry.get("type") != "shortcut":
			insert_at = idx
			break

	if found:
		return json.dumps(content), False

	content.insert(
		insert_at,
		{
			"id": generate_hash(length=10),
			"type": "shortcut",
			"data": {
				"shortcut_name": SHORTCUT_LABEL,
				"col": 3,
			},
		},
	)
	return json.dumps(content), True
