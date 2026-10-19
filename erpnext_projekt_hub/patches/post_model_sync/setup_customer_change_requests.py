import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import generate_hash

WORKSPACE_NAME = "Projects"
REQUEST_SHORTCUTS = (
	("Customer Request", "Customer Request", "Blue"),
	("Change Request", "Change Request", "Green"),
)
PROJECT_HUB_SHORTCUT = ("Project Hub", "/project-hub", "Blue")

# "Project Manager" (kierownik projektu) handles requests like "Projects Manager".
PROJECT_MANAGER_ROLE = "Project Manager"
MANAGER_ROLES = ("Projects Manager", PROJECT_MANAGER_ROLE, "System Manager")
ALL_ROLES = ("Projects User", *MANAGER_ROLES)

# Analysis queue: requests waiting for analysis, and those nobody has taken yet.
# Whoever takes a request is kept in its `analyst` field (see request_queue.py).
# Filters use the 4-item form: the workspace widget drops the last filter of a
# list whose filters have 5 items (frappe.utils.cleanup_filters).
ANALYSIS_QUEUE_FILTERS = [["Customer Request", "workflow_state", "=", "To Analyze"]]
UNASSIGNED_ANALYSIS_FILTERS = [
	*ANALYSIS_QUEUE_FILTERS,
	["Customer Request", "analyst", "is", "not set"],
]
UNASSIGNED_CHANGE_ANALYSIS_FILTERS = [
	["Change Request", "workflow_state", "=", "Draft"],
	["Change Request", "analyst", "is", "not set"],
]
QUEUE_SHORTCUTS = (
	("Requests to Analyze", "Customer Request", "Orange", ANALYSIS_QUEUE_FILTERS, "{} to analyze"),
	("Unassigned Analyses", "Customer Request", "Red", UNASSIGNED_ANALYSIS_FILTERS, "{} unassigned"),
	(
		"Unassigned Change Requests",
		"Change Request",
		"Red",
		UNASSIGNED_CHANGE_ANALYSIS_FILTERS,
		"{} unassigned",
	),
)
CONTENT_SHORTCUT_LABELS = (
	[label for label, _, _ in REQUEST_SHORTCUTS]
	+ [label for label, *_ in QUEUE_SHORTCUTS]
	+ [PROJECT_HUB_SHORTCUT[0]]
)


def execute():
	ensure_task_custom_field()
	ensure_project_manager_role()
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
				},
				{
					"fieldname": "reference_link",
					"label": "Reference Link",
					"fieldtype": "Data",
					"description": "GitHub branch, documentation, or other reference URL for this task.",
					"insert_after": "milestone",
				},
			]
		},
		update=True,
	)


def ensure_project_manager_role():
	"""The workflows name this role; project_control creates it, a plain install may not."""
	if not frappe.db.exists("Role", PROJECT_MANAGER_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": PROJECT_MANAGER_ROLE, "desk_access": 1}).insert(
			ignore_permissions=True
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
				"Draft": ALL_ROLES,
				# The analysis is written by whoever takes the request from the
				# queue, usually a developer without a manager role.
				"To Analyze": ALL_ROLES,
				"Quoted": MANAGER_ROLES,
				"Accepted": MANAGER_ROLES,
				"Rejected": MANAGER_ROLES,
				"Converted": MANAGER_ROLES,
			}
		),
		"transitions": [
			*transitions("Draft", "Submit for Analysis", "To Analyze", ALL_ROLES),
			*transitions("To Analyze", "Mark Quoted", "Quoted", MANAGER_ROLES),
			*transitions("To Analyze", "Reject", "Rejected", MANAGER_ROLES),
			*transitions("Quoted", "Accept", "Accepted", MANAGER_ROLES),
			*transitions("Quoted", "Reject", "Rejected", MANAGER_ROLES),
			# Accepted -> Converted has no transition on purpose: only
			# CustomerRequest.create_change_request sets it, together with the
			# Change Request it creates.
			*transitions("Rejected", "Submit for Analysis", "To Analyze", ALL_ROLES),
		],
	}


def change_request_workflow():
	return {
		"states": state_rows(
			{
				"Draft": MANAGER_ROLES,
				"Approved": MANAGER_ROLES,
				"Task Created": MANAGER_ROLES,
				"Done": MANAGER_ROLES,
				"Cancelled": MANAGER_ROLES,
			}
		),
		"transitions": [
			*transitions("Draft", "Approve", "Approved", MANAGER_ROLES),
			*transitions("Task Created", "Mark Done", "Done", MANAGER_ROLES),
			*transitions("Task Created", "Cancel", "Cancelled", MANAGER_ROLES),
		],
	}


def state_rows(states_by_role):
	rows = []
	for state, roles in states_by_role.items():
		for role in roles:
			rows.append({"state": state, "doc_status": "0", "allow_edit": role})
	return rows


def transitions(state, action, next_state, roles):
	return [
		{
			"state": state,
			"action": action,
			"next_state": next_state,
			"allowed": role,
			"allow_self_approval": 1,
		}
		for role in roles
	]


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

	for label, doctype, color, filters, count_format in QUEUE_SHORTCUTS:
		if ensure_workspace_filtered_shortcut(workspace, label, doctype, color, filters, count_format):
			changed = True

	if ensure_workspace_url_shortcut(workspace, *PROJECT_HUB_SHORTCUT):
		changed = True

	if ensure_workspace_link_cleanup(workspace, PROJECT_HUB_SHORTCUT[0], PROJECT_HUB_SHORTCUT[1]):
		changed = True

	content = workspace.content
	content_changed = False
	for label in CONTENT_SHORTCUT_LABELS:
		content, shortcut_changed = ensure_shortcut_in_content(content, label)
		if shortcut_changed:
			content_changed = True

	if content_changed:
		workspace.content = content
		changed = True

	if changed:
		workspace.flags.ignore_links = True
		workspace.save(ignore_permissions=True)


def ensure_workspace_shortcut(workspace, label, doctype, color):
	for row in workspace.shortcuts:
		# Filtered shortcuts (the analysis queue) link to the same doctype.
		if (row.link_to == doctype and not row.stats_filter) or row.label == label:
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


def ensure_workspace_filtered_shortcut(workspace, label, doctype, color, filters, count_format):
	"""A list shortcut that opens with `filters` applied and shows their count."""
	values = {
		"type": "DocType",
		"link_to": doctype,
		"doc_view": "List",
		"stats_filter": json.dumps(filters),
		"format": count_format,
	}
	for row in workspace.shortcuts:
		if row.label == label:
			changed = False
			for fieldname, value in values.items():
				if row.get(fieldname) != value:
					row.set(fieldname, value)
					changed = True
			return changed

	workspace.append("shortcuts", {"label": label, "color": color, **values})
	return True


def ensure_workspace_url_shortcut(workspace, label, url, color):
	for row in workspace.shortcuts:
		if row.label == label or row.url == url or row.link_to == url:
			changed = False
			if row.label != label:
				row.label = label
				changed = True
			if row.type != "URL":
				row.type = "URL"
				changed = True
			if row.url != url:
				row.url = url
				changed = True
			if row.link_to:
				row.link_to = None
				changed = True
			if row.doc_view != "List":
				row.doc_view = "List"
				changed = True
			if row.color != color:
				row.color = color
				changed = True
			return changed

	workspace.append(
		"shortcuts",
		{
			"type": "URL",
			"label": label,
			"url": url,
			"color": color,
			"doc_view": "List",
		},
	)
	return True


def ensure_workspace_link_cleanup(workspace, label, url):
	changed = False
	for row in list(workspace.links):
		if row.label == label or row.link_to in (url, "project-hub"):
			workspace.remove(row)
			changed = True
	return changed


def ensure_shortcut_in_content(raw_content, shortcut_label):
	if not raw_content:
		content = []
	else:
		try:
			content = json.loads(raw_content)
		except json.JSONDecodeError:
			return raw_content, False

	changed = False
	existing = {
		(entry.get("data") or {}).get("shortcut_name") for entry in content if entry.get("type") == "shortcut"
	}

	if shortcut_label in existing:
		return json.dumps(content), False

	block = {
		"id": generate_hash(length=10),
		"type": "shortcut",
		"data": {
			"shortcut_name": shortcut_label,
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
	changed = True

	return json.dumps(content), changed
