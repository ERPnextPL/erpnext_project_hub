import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.www import project_hub


class TestProjectHubPlugins(FrappeTestCase):
	def test_plugin_bundles_get_asset_urls_with_a_version_that_follows_their_content(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			bundle = root / "some_plugin" / "public" / "frontend"
			bundle.mkdir(parents=True)
			(bundle / "tabs.js").write_text("console.log('tabs v1');\n", encoding="utf-8")
			(bundle / "tabs.css").write_text(".tab { color: red; }\n", encoding="utf-8")

			hooks = [{"js": "some_plugin/frontend/tabs.js", "css": "some_plugin/frontend/tabs.css"}]

			def fake_get_app_path(*parts):
				return str(root.joinpath(*parts))

			with (
				patch("erpnext_projekt_hub.www.project_hub.frappe.get_hooks", return_value=hooks),
				patch(
					"erpnext_projekt_hub.www.project_hub.frappe.get_app_path", side_effect=fake_get_app_path
				),
			):
				plugins = project_hub.get_plugins()
				(bundle / "tabs.js").write_text("console.log('tabs v2');\n", encoding="utf-8")
				updated_plugins = project_hub.get_plugins()

		version = plugins[0]["js"].partition("?v=")[2]
		self.assertEqual(
			plugins,
			[
				{
					"js": f"/assets/some_plugin/frontend/tabs.js?v={version}",
					"css": f"/assets/some_plugin/frontend/tabs.css?v={version}",
				}
			],
		)
		self.assertNotEqual(updated_plugins[0]["js"], plugins[0]["js"])

	def test_no_plugins_without_an_installed_app_that_registers_one(self):
		with patch("erpnext_projekt_hub.www.project_hub.frappe.get_hooks", return_value=[]):
			self.assertEqual(project_hub.get_plugins(), [])


class TestProjectHubAssetVersion(FrappeTestCase):
	def test_css_changes_refresh_the_asset_version_token_when_mtime_is_preserved(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			assets = root / "erpnext_projekt_hub" / "public" / "frontend" / "assets"
			assets.mkdir(parents=True)

			(assets / "main.js").write_text("console.log('main v1');\n", encoding="utf-8")
			(assets / "index.css").write_text("body { color: red; }\n", encoding="utf-8")
			(assets / "frappe-ui.css").write_text(".btn { color: blue; }\n", encoding="utf-8")

			def fake_get_app_path(*parts):
				return str(root.joinpath(*parts))

			with patch(
				"erpnext_projekt_hub.www.project_hub.frappe.get_app_path", side_effect=fake_get_app_path
			):
				first_token = project_hub.get_asset_version()

				css_path = assets / "index.css"
				mtime_ns = css_path.stat().st_mtime_ns
				css_path.write_text("body { color: green; }\n", encoding="utf-8")
				os.utime(css_path, ns=(mtime_ns, mtime_ns))
				second_token = project_hub.get_asset_version()

		self.assertNotEqual(first_token, second_token)
