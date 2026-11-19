import frappe

from erpnext_projekt_hub.patches.post_model_sync.backfill_customer_request_state_changed_on import (
	latest_state_changes,
)

# Approving a Change Request creates its task and moves it on to Task Created
# without a version, so the task's creation dates that state.
TASK_STATES = ("Approved", "Task Created")


def execute():
	"""Fill Change Request.state_changed_on for requests created before the field.

	The date comes from the latest workflow_state change in the version log,
	or from the created task for a request that stopped at Task Created, and
	falls back to the request's creation.
	"""
	requests = frappe.get_all(
		"Change Request",
		filters={"state_changed_on": ["is", "not set"]},
		fields=["name", "workflow_state", "task", "creation"],
	)
	if not requests:
		return

	state_changes = latest_state_changes([row.name for row in requests], "Change Request")
	task_names = [row.task for row in requests if row.task]
	tasks_created = {}
	if task_names:
		tasks_created = dict(
			frappe.get_all(
				"Task",
				filters={"name": ["in", task_names]},
				fields=["name", "creation"],
				as_list=True,
			)
		)

	for row in requests:
		changed_on = None
		if row.workflow_state in TASK_STATES:
			changed_on = tasks_created.get(row.task)
		changed_on = changed_on or state_changes.get(row.name) or row.creation
		frappe.db.set_value("Change Request", row.name, "state_changed_on", changed_on, update_modified=False)
