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
	Po instalacji projekt_hub - dodaj skrót do Project Hub w workspace Projects
	"""
	try:
		# Sprawdź, czy workspace Projects istnieje
		if frappe.db.exists('Workspace', 'Projects'):
			ws = frappe.get_doc('Workspace', 'Projects')
			
			# Sprawdź, czy link już istnieje
			existing_link = None
			for link in ws.links:
				if link.link_to == '/project-hub':
					existing_link = link
					break
			
			# Dodaj link jeśli nie istnieje
			if not existing_link:
				ws.append('links', {
					'type': 'Link',
					'link_to': '/project-hub',
					'label': 'Project Hub',
					'icon': 'folder',
					'color': 'Blue',
					'description': 'Access the Project Hub interface'
				})
				ws.save()
				frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"Error adding Project Hub link during installation: {str(e)}", "Installation Error")
