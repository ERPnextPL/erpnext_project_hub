import frappe

def setup_system_settings():
    """
    Setup basic system settings for the site
    """
    try:
        # Get or create System Settings
        if frappe.db.exists("System Settings", "System Settings"):
            doc = frappe.get_doc("System Settings", "System Settings")
        else:
            doc = frappe.new_doc("System Settings")
            doc.name = "System Settings"
        
        # Set required fields
        doc.language = "pl"
        doc.time_zone = "Europe/Warsaw"
        doc.enable_scheduler = 1
        doc.setup_complete = 1
        doc.save(ignore_permissions=True)
        
        frappe.db.commit()
        print("System Settings configured successfully")
        
    except Exception as e:
        frappe.log_error(f"Error setting up System Settings: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_system_settings()
