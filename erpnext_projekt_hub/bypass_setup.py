import frappe

def bypass_setup_wizard():
    """
    Complete setup wizard bypass by setting all required flags
    """
    try:
        # Get System Settings
        doc = frappe.get_doc("System Settings", "System Settings")
        
        # Set all setup completion flags
        doc.setup_complete = 1
        doc.enable_onboarding = 0
        doc.country = "Poland"
        doc.currency = "PLN"
        doc.save(ignore_permissions=True)
        
        print("Setup wizard bypass completed successfully")
        
    except Exception as e:
        frappe.log_error(f"Error bypassing setup wizard: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    bypass_setup_wizard()
