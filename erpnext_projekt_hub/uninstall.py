from pathlib import Path

PRO_ENABLED_MARKER = Path(__file__).resolve().parents[1] / "frontend" / ".pro-enabled"


def after_uninstall():
	"""Remove the PRO frontend marker when the app is uninstalled."""
	if PRO_ENABLED_MARKER.exists():
		PRO_ENABLED_MARKER.unlink()
