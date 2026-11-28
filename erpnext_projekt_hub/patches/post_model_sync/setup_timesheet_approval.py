from erpnext_projekt_hub.timesheet_approval import setup


def execute():
	"""Add the Timesheet approval workflow and fill workflow_state on existing timesheets:
	drafts stay Draft, submitted ones become Approved, cancelled ones Cancelled."""
	setup()
