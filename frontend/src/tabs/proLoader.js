/**
 * PRO tab loader
 *
 * Loads PRO tab registrations via a runtime hook instead of a hard build-time
 * dependency. This keeps the core app functional even when the PRO bundle is
 * deployed separately or core assets are rebuilt.
 */

function getWindow() {
	return typeof window !== "undefined" ? window : null;
}

function getBootInfo() {
	const win = getWindow();
	return win?.frappe?.boot || {};
}

export function isProTabsAvailable() {
	const boot = getBootInfo();
	return Boolean(
		boot.project_hub_pro_enabled ||
			boot.has_pro_license ||
			boot.installed_apps?.includes?.("projekt_hub_pro") ||
			boot.installed_apps?.includes?.("erpnext_projekt_hub_pro")
	);
}

export async function loadProTabs(registerCoreTabsFn) {
	const win = getWindow();

	// Allow PRO bundles to register themselves through a public global hook.
	const globalRegister = win?.__PROJECT_HUB_PRO_REGISTER_TABS__;
	if (typeof globalRegister === "function") {
		try {
			await Promise.resolve(globalRegister(registerCoreTabsFn));
			return true;
		} catch (error) {
			console.error("PRO tab registration hook failed", error);
		}
	}

	// Support boot-time hook provided by a PRO app if it wants to expose
	// registration without polluting the global namespace.
	const bootRegister = getBootInfo().project_hub_pro_register_tabs;
	if (typeof bootRegister === "function") {
		try {
			await Promise.resolve(bootRegister(registerCoreTabsFn));
			return true;
		} catch (error) {
			console.error("PRO boot tab registration hook failed", error);
		}
	}

	return false;
}
