import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.www import project_hub


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
