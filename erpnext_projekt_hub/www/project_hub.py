"""
Project Hub page controller.
"""

import hashlib
import os

import frappe
from frappe import _
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

# (mtimes, token) of the last hashed build, so the files are only re-read when
# they change.
_asset_version_cache: tuple[tuple[float, ...], str] | None = None


def get_asset_version() -> str:
	"""Return a cache-busting token derived from the built assets.

	Hashes the file contents rather than using mtimes so every node of a
	multi-server deployment serves the same token for the same build.
	"""
	global _asset_version_cache

	paths = [frappe.get_app_path(*entry) for entry in ASSET_ENTRIES]

	try:
		mtimes = tuple(os.path.getmtime(path) for path in paths)
	except OSError:
		# No build on disk - the page is broken anyway, so just avoid caching it.
		return frappe.generate_hash(length=10)

	if _asset_version_cache and _asset_version_cache[0] == mtimes:
		return _asset_version_cache[1]

	hasher = hashlib.sha1(usedforsecurity=False)

	try:
		# Paths are derived from the hardcoded ASSET_ENTRIES tuple, not user input.
		for path in paths:
			with open(path, "rb") as bundle:  # nosemgrep
				hasher.update(bundle.read())
				hasher.update(b"\0")
	except OSError:
		return frappe.generate_hash(length=10)

	token = hasher.hexdigest()[:10]
	_asset_version_cache = (mtimes, token)
	return token


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
	context.asset_version = get_asset_version()

	return context
