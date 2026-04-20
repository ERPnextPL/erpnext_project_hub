from __future__ import annotations

import frappe


def execute():
	milestones = frappe.get_all(
		"Project Milestone",
		filters={"milestone_name": ["in", ["", None]]},
		fields=["name", "milestone_name"],
		limit_page_length=0,
	)

	for milestone in milestones:
		frappe.db.set_value(
			"Project Milestone",
			milestone.name,
			"milestone_name",
			milestone.name,
			update_modified=False,
		)
