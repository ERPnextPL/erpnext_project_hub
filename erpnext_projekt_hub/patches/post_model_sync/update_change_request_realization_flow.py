import frappe
from frappe.desk.form.assign_to import close_all_assignments

from erpnext_projekt_hub.patches.post_model_sync import setup_customer_change_requests


def execute():
	"""Move Change Requests from the old analysis queue into the realization flow."""
	setup_customer_change_requests.execute()

	draft_requests = frappe.get_all("Change Request", filters={"workflow_state": "Draft"}, pluck="name")
	for name in draft_requests:
		close_all_assignments("Change Request", name, ignore_permissions=True)
