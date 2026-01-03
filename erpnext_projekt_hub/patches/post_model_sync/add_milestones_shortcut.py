import json

import frappe
from frappe.utils import generate_hash


WORKSPACE_NAME = "Projects"
SHORTCUT_LABEL = "Project Milestone"
SHORTCUT_DOCTYPE = "Project Milestone"
LEGACY_SHORTCUT_LABELS = {"Milestones"}


def execute():
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = ensure_workspace_shortcut(workspace)

	content, content_changed = ensure_shortcut_in_content(workspace.content)
	if content_changed:
		workspace.content = content
		changed = True

	if changed:
		workspace.save(ignore_permissions=True)


def ensure_workspace_shortcut(workspace):
	changed = False
	primary_row = None
	duplicates = []

	for row in workspace.shortcuts:
		if row.link_to == SHORTCUT_DOCTYPE or row.label in LEGACY_SHORTCUT_LABELS or row.label == SHORTCUT_LABEL:
			if primary_row:
				duplicates.append(row)
			else:
				primary_row = row

	if primary_row:
		if primary_row.label != SHORTCUT_LABEL:
			primary_row.label = SHORTCUT_LABEL
			changed = True
		if primary_row.link_to != SHORTCUT_DOCTYPE:
			primary_row.link_to = SHORTCUT_DOCTYPE
			changed = True
		if primary_row.type != "DocType":
			primary_row.type = "DocType"
			changed = True
		if primary_row.doc_view != "List":
			primary_row.doc_view = "List"
			changed = True
	else:
		workspace.append(
			"shortcuts",
			{
				"type": "DocType",
				"link_to": SHORTCUT_DOCTYPE,
				"label": SHORTCUT_LABEL,
				"color": "Purple",
				"doc_view": "List",
			},
		)
		changed = True

	for row in duplicates:
		workspace.remove(row)
		changed = True

	return changed


def ensure_shortcut_in_content(raw_content):
	if not raw_content:
		content = []
	else:
		try:
			content = json.loads(raw_content)
		except json.JSONDecodeError:
			content = []

	content_changed = False
	found = False
	indices_to_remove = []

	for idx, entry in enumerate(content):
		if entry.get("type") != "shortcut":
			continue

		name = entry.get("data", {}).get("shortcut_name")
		if name == SHORTCUT_LABEL:
			if found:
				indices_to_remove.append(idx)
				content_changed = True
			else:
				found = True
		elif name in LEGACY_SHORTCUT_LABELS:
			if found:
				indices_to_remove.append(idx)
			else:
				entry["data"]["shortcut_name"] = SHORTCUT_LABEL
				found = True
			content_changed = True

	for idx in reversed(indices_to_remove):
		content.pop(idx)

	if found:
		return json.dumps(content), content_changed

	block = {
		"id": generate_hash(length=10),
		"type": "shortcut",
		"data": {
			"shortcut_name": SHORTCUT_LABEL,
			"col": 3,
		},
	}

	insert_at = len(content)
	visible_shortcut_area = False

	for idx, entry in enumerate(content):
		if entry.get("type") == "header":
			text = (entry.get("data") or {}).get("text", "")
			if "Your Shortcuts" in text:
				visible_shortcut_area = True
			continue

		if visible_shortcut_area and entry.get("type") != "shortcut":
			insert_at = idx
			break

	content.insert(insert_at, block)
	return json.dumps(content), True
