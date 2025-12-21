import frappe

def add_project_hub_link():
	"""Add Project Hub link to Projects workspace"""
	try:
		# Get the Projects workspace
		ws = frappe.get_doc('Workspace', 'Projects')
		
		# Check if link already exists
		existing_link = None
		for link in ws.links:
			if link.link_to == '/project-hub':
				existing_link = link
				break
		
		if not existing_link:
			# Add new link
			ws.append('links', {
				'type': 'Link',
				'link_to': '/project-hub',
				'label': 'Project Hub',
				'icon': 'folder',
				'color': 'Blue',
				'description': 'Access the Project Hub interface'
			})
			ws.save()
			print("Project Hub link added to Projects workspace")
		else:
			print("Project Hub link already exists")
			
	except Exception as e:
		print(f"Error: {str(e)}")
		frappe.log_error(f"Error adding Project Hub link: {str(e)}", "Workspace Link Error")

if __name__ == "__main__":
	add_project_hub_link()
