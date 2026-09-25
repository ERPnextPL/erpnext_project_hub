"""
Project Hub page controller.
"""

import hashlib

import frappe
from frappe import _
from frappe.translate import get_translations_from_apps
from frappe.website.utils import get_boot_data

from erpnext_projekt_hub.access import has_project_hub_access

no_cache = 1

# Fixed entry files of the SPA build. Vite hashes the lazy-loaded chunks but not
# these, and Frappe serves /assets with a 12 hour max-age, so without a
# cache-busting token a browser can keep running a stale bundle long after a
# deploy.
ASSET_ENTRIES = (
	("erpnext_projekt_hub", "public", "frontend", "assets", "main.js"),
	("erpnext_projekt_hub", "public", "frontend", "assets", "index.css"),
	("erpnext_projekt_hub", "public", "frontend", "assets", "frappe-ui.css"),
)


def get_asset_version(entries=ASSET_ENTRIES) -> str:
	"""Return a cache-busting token derived from the built assets.

	Hashes the current file contents so deployments that preserve mtimes still
	produce a new token when an asset changes.
	"""
	paths = [frappe.get_app_path(*entry) for entry in entries]

	try:
		# Paths come from ASSET_ENTRIES or from apps' hooks.py, not user input.
		hasher = hashlib.sha1(usedforsecurity=False)
		for path in paths:
			with open(path, "rb") as bundle:  # nosemgrep
				hasher.update(bundle.read())
				hasher.update(b"\0")
	except OSError:
		return frappe.generate_hash(length=10)

	return hasher.hexdigest()[:10]


def get_plugins() -> list[dict]:
	"""Return the frontend plugins (extra tabs) of the apps installed on this site.

	An app registers a prebuilt bundle in its hooks.py, with paths under /assets:
	    projekt_hub_plugins = [{"js": "<app>/frontend/tabs.js", "css": "<app>/frontend/tabs.css"}]
	frappe.get_hooks() only reads the hooks of apps installed on the current site,
	so a paid plugin deployed to a shared bench stays off for sites without it.
	See frontend/src/plugins.js for how the bundles are loaded.
	"""
	plugins = []
	for plugin in frappe.get_hooks("projekt_hub_plugins"):
		files = {kind: plugin[kind] for kind in ("js", "css") if plugin.get(kind)}
		if "js" not in files:
			continue

		version = get_asset_version(
			[(app, "public", *parts) for app, *parts in (path.split("/") for path in files.values())]
		)
		plugins.append({kind: f"/assets/{path}?v={version}" for kind, path in files.items()})

	return plugins


def get_context(context):
	"""Set up context for the project hub page."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access Projekt HUB"), frappe.PermissionError)

	if not has_project_hub_access():
		frappe.throw(_("You do not have permission to access Projekt HUB"), frappe.PermissionError)

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True

	# Pass CSRF token and boot data to template
	context.csrf_token = frappe.session.csrf_token
	context.boot = get_boot_data()
	# Scoped to this app's own translations file, not the site-wide dictionary
	# (get_messages_for_boot), which would drag in every installed app's strings.
	context.boot["messages"] = get_translations_from_apps(frappe.local.lang, apps=["erpnext_projekt_hub"])
	context.boot["projekt_hub_plugins"] = get_plugins()
	# Exposed as frappe.user_roles by project-hub.html, as desk does from its own boot.
	context.boot["user_roles"] = frappe.get_roles()
	context.asset_version = get_asset_version()

	return context
