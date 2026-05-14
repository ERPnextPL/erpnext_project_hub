import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import generate_hash

WORKSPACE_NAME = "Projects"
REQUEST_SHORTCUTS = (
	("Customer Request", "Customer Request", "Blue"),
	("Change Request", "Change Request", "Green"),
)


def execute():
	ensure_task_custom_field()
	ensure_workflow_prerequisites()
	ensure_workflow("Customer Request Workflow", "Customer Request", customer_request_workflow())
	ensure_workflow("Change Request Workflow", "Change Request", change_request_workflow())
	ensure_workspace_shortcuts()


def ensure_task_custom_field():
	create_custom_fields(
		{
			"Task": [
				{
					"fieldname": "change_request",
					"label": "Change Request",
					"fieldtype": "Link",
					"options": "Change Request",
					"insert_after": "project",
					"read_only": 1,
					"no_copy": 1,
				}
			]
		},
		update=True,
	)


def ensure_workflow_prerequisites():
	states = {
		"Draft": "",
		"To Analyze": "Primary",
		"Quoted": "Info",
		"Accepted": "Success",
		"Rejected": "Danger",
		"Converted": "Success",
		"Approved": "Success",
		"Task Created": "Info",
		"Done": "Success",
		"Cancelled": "Inverse",
	}
	for state, style in states.items():
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{
					"doctype": "Workflow State",
					"workflow_state_name": state,
					"style": style,
				}
			).insert(ignore_permissions=True)

	actions = (
		"Submit for Analysis",
		"Mark Quoted",
		"Accept",
		"Reject",
		"Mark Converted",
		"Approve",
		"Mark Done",
		"Cancel",
	)
	for action in actions:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{
					"doctype": "Workflow Action Master",
					"workflow_action_name": action,
				}
			).insert(ignore_permissions=True)


def customer_request_workflow():
	return {
		"states": state_rows(
			{
				"Draft": ("Projects User", "Projects Manager", "System Manager"),
				"To Analyze": ("Projects Manager", "System Manager"),
				"Quoted": ("Projects Manager", "System Manager"),
				"Accepted": ("Projects Manager", "System Manager"),
				"Rejected": ("Projects Manager", "System Manager"),
				"Converted": ("Projects Manager", "System Manager"),
			}
		),
		"transitions": [
			transition("Draft", "Submit for Analysis", "To Analyze", "Projects User"),
			transition("Draft", "Submit for Analysis", "To Analyze", "Projects Manager"),
			transition("Draft", "Submit for Analysis", "To Analyze", "System Manager"),
			transition("To Analyze", "Mark Quoted", "Quoted", "Projects Manager"),
			transition("To Analyze", "Mark Quoted", "Quoted", "System Manager"),
			transition("To Analyze", "Reject", "Rejected", "Projects Manager"),
			transition("To Analyze", "Reject", "Rejected", "System Manager"),
			transition("Quoted", "Accept", "Accepted", "Projects Manager"),
			transition("Quoted", "Accept", "Accepted", "System Manager"),
			transition("Quoted", "Reject", "Rejected", "Projects Manager"),
			transition("Quoted", "Reject", "Rejected", "System Manager"),
			transition("Accepted", "Mark Converted", "Converted", "Projects Manager"),
			transition("Accepted", "Mark Converted", "Converted", "System Manager"),
			transition("Rejected", "Submit for Analysis", "To Analyze", "Projects User"),
			transition("Rejected", "Submit for Analysis", "To Analyze", "Projects Manager"),
			transition("Rejected", "Submit for Analysis", "To Analyze", "System Manager"),
		],
	}


def change_request_workflow():
	return {
		"states": state_rows(
			{
				"Draft": ("Projects Manager", "System Manager"),
				"Approved": ("Projects Manager", "System Manager"),
				"Task Created": ("Projects Manager", "System Manager"),
				"Done": ("Projects Manager", "System Manager"),
				"Cancelled": ("Projects Manager", "System Manager"),
			}
		),
		"transitions": [
			transition("Draft", "Approve", "Approved", "Projects Manager"),
			transition("Draft", "Approve", "Approved", "System Manager"),
			transition("Task Created", "Mark Done", "Done", "Projects Manager"),
			transition("Task Created", "Mark Done", "Done", "System Manager"),
			transition("Task Created", "Cancel", "Cancelled", "Projects Manager"),
			transition("Task Created", "Cancel", "Cancelled", "System Manager"),
		],
	}


def state_rows(states_by_role):
	rows = []
	for state, roles in states_by_role.items():
		for role in roles:
			rows.append({"state": state, "doc_status": "0", "allow_edit": role})
	return rows


def transition(state, action, next_state, role):
	return {
		"state": state,
		"action": action,
		"next_state": next_state,
		"allowed": role,
		"allow_self_approval": 1,
	}


def ensure_workflow(workflow_name, document_type, config):
	if frappe.db.exists("Workflow", workflow_name):
		workflow = frappe.get_doc("Workflow", workflow_name)
	else:
		workflow = frappe.new_doc("Workflow")
		workflow.workflow_name = workflow_name

	workflow.document_type = document_type
	workflow.workflow_state_field = "workflow_state"
	workflow.is_active = 1
	workflow.send_email_alert = 0
	workflow.set("states", config["states"])
	workflow.set("transitions", config["transitions"])
	workflow.save(ignore_permissions=True)


def ensure_workspace_shortcuts():
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = False

	for label, doctype, color in REQUEST_SHORTCUTS:
		if ensure_workspace_shortcut(workspace, label, doctype, color):
			changed = True

	content, content_changed = ensure_shortcuts_in_content(workspace.content)
	if content_changed:
		workspace.content = content
		changed = True

	if changed:
		workspace.flags.ignore_links = True
		workspace.save(ignore_permissions=True)


def ensure_workspace_shortcut(workspace, label, doctype, color):
	for row in workspace.shortcuts:
		if row.link_to == doctype or row.label == label:
			changed = False
			if row.label != label:
				row.label = label
				changed = True
			if row.link_to != doctype:
				row.link_to = doctype
				changed = True
			if row.type != "DocType":
				row.type = "DocType"
				changed = True
			if row.doc_view != "List":
				row.doc_view = "List"
				changed = True
			return changed

	workspace.append(
		"shortcuts",
		{
			"type": "DocType",
			"link_to": doctype,
			"label": label,
			"color": color,
			"doc_view": "List",
		},
	)
	return True


def ensure_shortcuts_in_content(raw_content):
	if not raw_content:
		content = []
	else:
		try:
			content = json.loads(raw_content)
		except json.JSONDecodeError:
			content = []

	changed = False
	existing = {
		(entry.get("data") or {}).get("shortcut_name") for entry in content if entry.get("type") == "shortcut"
	}

	for label, _doctype, _color in REQUEST_SHORTCUTS:
		if label in existing:
			continue

		content.append(
			{
				"id": generate_hash(length=10),
				"type": "shortcut",
				"data": {
					"shortcut_name": label,
					"col": 3,
				},
			}
		)
		changed = True

	return json.dumps(content), changed
