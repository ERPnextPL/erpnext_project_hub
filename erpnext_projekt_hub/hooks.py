app_name = "erpnext_projekt_hub"
app_title = "Projekt HUB"
app_publisher = "Krzysztof"
app_description = "New Project design in ERPnext"
app_email = "krzysztof@erpetch.pl"
app_license = "mit"

export_python_type_annotations = True

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "erpnext_projekt_hub",
		"logo": "/assets/erpnext_projekt_hub/logo-hub.svg",
		"title": "Projekt HUB",
		"route": "/project-hub",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	"/assets/erpnext_projekt_hub/css/kanban_custom.css",
	"/assets/erpnext_projekt_hub/css/erpnext_projekt_hub.css",
]
app_include_js = "/assets/erpnext_projekt_hub/js/kanban_custom.js"

# include js, css files in header of web template
web_include_css = "/assets/erpnext_projekt_hub/css/erpnext_projekt_hub.css"
# web_include_js = "/assets/erpnext_projekt_hub/js/erpnext_projekt_hub.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpnext_projekt_hub/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Project": "public/js/project.js", "Timesheet": "public/js/timesheet_timer_override.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Website route rules for SPA
website_route_rules = [
	{"from_route": "/project-hub/<path:app_path>", "to_route": "project-hub"},
]

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "erpnext_projekt_hub/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "erpnext_projekt_hub.utils.jinja_methods",
# 	"filters": "erpnext_projekt_hub.utils.jinja_filters"
# }

# Installation
# ------------

before_install = "erpnext_projekt_hub.install.before_install"
after_install = "erpnext_projekt_hub.install.after_install"
# Uninstallation
# ------------

# before_uninstall = "erpnext_projekt_hub.uninstall.before_uninstall"
# after_uninstall = "erpnext_projekt_hub.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "erpnext_projekt_hub.utils.before_app_install"
# after_app_install = "erpnext_projekt_hub.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "erpnext_projekt_hub.utils.before_app_uninstall"
# after_app_uninstall = "erpnext_projekt_hub.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_projekt_hub.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Task": {
		"before_validate": "erpnext_projekt_hub.events.task_events.before_validate_task",
		"validate": "erpnext_projekt_hub.events.task_events.validate_task_due_dates",
		"on_update": "erpnext_projekt_hub.events.task_events.on_task_update",
		"on_trash": "erpnext_projekt_hub.events.task_events.on_task_trash",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnext_projekt_hub.tasks.all"
# 	],
# 	"daily": [
# 		"erpnext_projekt_hub.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnext_projekt_hub.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnext_projekt_hub.tasks.weekly"
# 	],
# 	"monthly": [
# 		"erpnext_projekt_hub.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "erpnext_projekt_hub.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnext_projekt_hub.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpnext_projekt_hub.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["erpnext_projekt_hub.utils.before_request"]
after_request = ["erpnext_projekt_hub.api.pwa.add_sw_allowed_header"]

# Job Events
# ----------
# before_job = ["erpnext_projekt_hub.utils.before_job"]
# after_job = ["erpnext_projekt_hub.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"erpnext_projekt_hub.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

# Fixtures
# --------
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["name", "in", ["Task-milestone", "Project-project_manager", "Project-documentation_url"]]
		],
	},
	{
		"dt": "Workspace Link",
		"filters": [["parent", "=", "Projects"], ["label", "in", ["Project Hub", "Project Milestone"]]],
	},
	{
		"dt": "Workspace Shortcut",
		"filters": [["parent", "=", "Projects"], ["link_to", "=", "Project Milestone"]],
	},
	{"dt": "Workspace Shortcut", "filters": [["parent", "=", "Projects"], ["link_to", "=", "/project-hub"]]},
]
