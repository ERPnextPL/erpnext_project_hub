from erpnext_projekt_hub.patches.post_model_sync import setup_customer_change_requests


def execute():
	# Re-sync the request workflows (To Analyze editable by Projects User, no
	# "Mark Converted") and add the analysis queue shortcuts to the workspace.
	setup_customer_change_requests.execute()
