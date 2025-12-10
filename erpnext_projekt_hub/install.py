import frappe

def before_install():
    """
    Sprawdź, czy erpnext jest zainstalowane przed instalacją projekt_hub
    """
    installed_apps = frappe.get_installed_apps()
    if "erpnext" not in installed_apps:
        frappe.throw("Aplikacja erpnext jest wymagana do zainstalowania Projekt HUB. Proszę zainstalować erpnext najpierw.")

def after_install():
    """
    Po instalacji projekt_hub
    """
    pass
