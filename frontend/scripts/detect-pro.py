"""
Detects whether projekt_hub_pro is installed on the default Frappe site.

Called by vite.config.js at build time via execFileSync.
Outputs "True" or "False" to stdout.  Exit code is always 0.

Reads DB credentials from site_config.json and queries the
`tabInstalled Application` table directly — no frappe.init() needed,
so this works correctly regardless of the current working directory.
"""

import json
import os
import sys

# Resolve bench root: this file is at apps/erpnext_projekt_hub/frontend/scripts/
_this_dir = os.path.dirname(os.path.abspath(__file__))
bench_path = os.path.normpath(os.path.join(_this_dir, "..", "..", "..", ".."))


def _get_default_site():
	common_config = os.path.join(bench_path, "sites", "common_site_config.json")
	try:
		with open(  # nosemgrep: frappe-semgrep-rules.rules.security.frappe-security-file-traversal
			common_config
		) as f:
			config = json.load(f)
		site = config.get("default_site", "").rstrip("/")
		if site:
			return site
	except Exception:
		pass

	# Fallback: first directory in sites/ with a site_config.json
	sites_dir = os.path.join(bench_path, "sites")
	try:
		for entry in sorted(os.listdir(sites_dir)):
			if os.path.exists(os.path.join(sites_dir, entry, "site_config.json")):
				return entry
	except Exception:
		pass

	return None


def _get_site_config(site):
	site_config_path = os.path.join(bench_path, "sites", site, "site_config.json")
	common_config_path = os.path.join(bench_path, "sites", "common_site_config.json")

	config = {}
	try:
		with open(  # nosemgrep: frappe-semgrep-rules.rules.security.frappe-security-file-traversal
			common_config_path
		) as f:
			config.update(json.load(f))
	except Exception:
		pass
	try:
		with open(  # nosemgrep: frappe-semgrep-rules.rules.security.frappe-security-file-traversal
			site_config_path
		) as f:
			config.update(json.load(f))
	except Exception:
		pass
	return config


def main():
	site = _get_default_site()
	if not site:
		print("False")
		return

	config = _get_site_config(site)
	db_name = config.get("db_name")
	db_password = config.get("db_password", "")
	db_host = config.get("db_host", "127.0.0.1") or "127.0.0.1"
	try:
		db_port = int(config.get("db_port") or 3306)
	except (ValueError, TypeError):
		db_port = 3306
	db_type = config.get("db_type", "mariadb")

	if not db_name:
		print("False")
		return

	try:
		if db_type == "postgres":
			import psycopg2

			conn = psycopg2.connect(
				dbname=db_name,
				user=db_name,
				password=db_password,
				host=db_host,
				port=db_port,
			)
			cur = conn.cursor()
			cur.execute(
				'SELECT 1 FROM "tabInstalled Application" WHERE app_name = %s LIMIT 1',
				("projekt_hub_pro",),
			)
		else:
			import pymysql

			conn = pymysql.connect(
				database=db_name,
				user=db_name,
				password=db_password,
				host=db_host,
				port=db_port,
				connect_timeout=5,
			)
			cur = conn.cursor()
			cur.execute(
				"SELECT 1 FROM `tabInstalled Application` WHERE app_name = %s LIMIT 1",
				("projekt_hub_pro",),
			)

		row = cur.fetchone()
		conn.close()
		print("True" if row else "False")

	except Exception as e:
		sys.stderr.write(f"detect-pro: {e}\n")
		print("False")


if __name__ == "__main__":
	main()
