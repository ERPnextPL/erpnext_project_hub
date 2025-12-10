import frappe

def before_install():
    """
    Sprawdź, czy erpnext jest zainstalowane przed instalacją projekt_hub
    """
    if not frappe.db.exists("App", "erpnext"):
        frappe.throw("Aplikacja erpnext jest wymagana do zainstalowania Projekt HUB. Proszę zainstalować erpnext najpierw.")

def after_install():
    """
    Po instalacji projekt_hub
    """
    pass
