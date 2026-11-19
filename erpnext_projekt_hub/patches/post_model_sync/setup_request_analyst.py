import frappe

from erpnext_projekt_hub.patches.post_model_sync import setup_customer_change_requests
from erpnext_projekt_hub.request_queue import QUEUE_STATES


def execute():
	# Re-sync the workflows (Project Manager handles requests like Projects
	# Manager) and the queue shortcuts, which read the assignee fields.
	setup_customer_change_requests.execute()
	backfill_analysts()


def backfill_analysts():
	"""Backfill analysts on Customer Requests taken before the field existed."""
	doctype = "Customer Request"
	state = QUEUE_STATES[doctype]
	requests = frappe.get_all(
		doctype,
		filters={"workflow_state": state, "analyst": ("is", "not set"), "_assign": ("like", '%"%')},
		fields=["name", "_assign"],
	)
	for request in requests:
		assignees = frappe.parse_json(request._assign or "[]")
		if isinstance(assignees, list) and assignees:
			frappe.db.set_value(doctype, request.name, "analyst", assignees[0], update_modified=False)
