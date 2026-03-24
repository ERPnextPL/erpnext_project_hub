import frappe


def execute():
	"""Initialize sort_order for existing milestones, numbered per-project starting from 0."""
	milestones = frappe.get_all(
		"Project Milestone",
		fields=["name", "project", "milestone_date", "creation"],
		order_by="project asc, milestone_date asc, creation asc",
	)

	counter = {}
	for milestone in milestones:
		project = milestone["project"]
		idx = counter.get(project, 0)
		counter[project] = idx + 1
		frappe.db.set_value(
			"Project Milestone",
			milestone["name"],
			"sort_order",
			idx,
			update_modified=False,
		)
