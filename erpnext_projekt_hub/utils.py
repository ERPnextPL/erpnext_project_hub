import signal
import sys

import frappe

_patch_applied = False


def patch_sync_dashboards_on_request():
	"""
	Patch sync_dashboards to handle BrokenPipeError during setup wizard.
	This prevents crashes when stdout is closed by reverse proxies or timeouts.
	Called during before_request to ensure the patch is applied before any request.
	"""
	global _patch_applied

	if _patch_applied:
		return

	try:
		# Ignore SIGPIPE signal to prevent BrokenPipeError
		signal.signal(signal.SIGPIPE, signal.SIG_DFL)
	except (AttributeError, ValueError):
		# SIGPIPE is not available on Windows
		pass

	try:
		from frappe.utils import dashboard as dashboard_module

		def patched_sync_dashboards(app=None):
			"""Import, overwrite dashboards from `[app]/[app]_dashboard` with broken pipe handling"""
			apps = [app] if app else frappe.get_installed_apps()

			for app_name in apps:
				try:
					print(f"Updating Dashboard for {app_name}")
					sys.stdout.flush()
				except (BrokenPipeError, OSError):
					# Ignore broken pipe errors when stdout is closed
					pass

				for module_name in frappe.local.app_modules.get(app_name) or []:
					frappe.flags.in_import = True
					dashboard_module.make_records_in_module(app_name, module_name)
					frappe.flags.in_import = False

		# Apply the monkey patch
		dashboard_module.sync_dashboards = patched_sync_dashboards
		_patch_applied = True
	except Exception as e:
		frappe.log_error(f"Failed to patch sync_dashboards: {e}")
