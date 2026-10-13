import frappe

CONVERTED_STATE = "Converted"


def execute():
	"""Fill Customer Request.state_changed_on for requests created before the field.

	The date comes from the latest workflow_state change in the version log; a
	Converted request takes its Change Request's creation, because the
	conversion is written without a version. Anything else falls back to the
	request's creation.
	"""
	requests = frappe.get_all(
		"Customer Request",
		filters={"state_changed_on": ["is", "not set"]},
		fields=["name", "workflow_state", "change_request", "creation"],
	)
	if not requests:
		return

	state_changes = latest_state_changes([row.name for row in requests])
	change_request_names = [row.change_request for row in requests if row.change_request]
	change_requests_created = {}
	if change_request_names:
		change_requests_created = dict(
			frappe.get_all(
				"Change Request",
				filters={"name": ["in", change_request_names]},
				fields=["name", "creation"],
				as_list=True,
			)
		)

	for row in requests:
		changed_on = None
		if row.workflow_state == CONVERTED_STATE:
			changed_on = change_requests_created.get(row.change_request)
		changed_on = changed_on or state_changes.get(row.name) or row.creation
		frappe.db.set_value(
			"Customer Request", row.name, "state_changed_on", changed_on, update_modified=False
		)


def latest_state_changes(names):
	"""Return {request name: when its workflow_state last changed} from the version log."""
	versions = frappe.get_all(
		"Version",
		filters={
			"ref_doctype": "Customer Request",
			"docname": ["in", names],
			"data": ["like", "%workflow_state%"],
		},
		fields=["docname", "data", "creation"],
		order_by="creation desc",
	)

	changed_on = {}
	for version in versions:
		if version.docname in changed_on:
			continue
		data = frappe.parse_json(version.data or "{}") or {}
		if any(change and change[0] == "workflow_state" for change in data.get("changed") or []):
			changed_on[version.docname] = version.creation
	return changed_on
