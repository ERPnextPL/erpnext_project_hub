import frappe
from frappe.desk.form.assign_to import close_all_assignments

from erpnext_projekt_hub.patches.post_model_sync import setup_customer_change_requests


def execute():
	"""Move Change Requests from the old analysis queue into the realization flow."""
	setup_customer_change_requests.execute()
	migrate_draft_change_request_assignees()


def migrate_draft_change_request_assignees():
	"""Preserve old Draft analysts as realization assignees before closing old ToDos."""
	draft_requests = frappe.get_all(
		"Change Request",
		filters={"workflow_state": "Draft"},
		fields=["name", "analyst", "realization_assignee"],
	)
	for request in draft_requests:
		if request.analyst and not request.realization_assignee:
			frappe.db.set_value(
				"Change Request",
				request.name,
				"realization_assignee",
				request.analyst,
				update_modified=False,
			)
		close_all_assignments("Change Request", request.name, ignore_permissions=True)
