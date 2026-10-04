from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Project-project_manager was shipped as a fixture in Feb 2026 and dropped from
# fixtures in March, while _is_project_manager_user() still relies on it.
# Create it in code so fresh installs and later fixture exports can't lose it.
PROJECT_CUSTOM_FIELDS = {
	"Project": [
		{
			"fieldname": "project_manager",
			"label": "Project Manager",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "department",
			"description": "User responsible for project management",
		}
	]
}


def execute():
	create_custom_fields(PROJECT_CUSTOM_FIELDS, update=True)
