"""
Project Outliner API endpoints for task management.
Provides CRUD operations for tasks in a hierarchical tree view.
"""

import frappe
from frappe import _
from frappe.utils import cint, today


def _get_incomplete_subtasks(task_name: str) -> list:
	"""
	Get all incomplete subtasks (recursively) for a given task.
	Returns list of dicts with name and subject.
	"""
	incomplete = []

	subtasks = frappe.get_all(
		"Task", filters={"parent_task": task_name}, fields=["name", "subject", "status"]
	)

	for subtask in subtasks:
		if subtask["status"] not in ["Completed", "Cancelled"]:
			incomplete.append({"name": subtask["name"], "subject": subtask["subject"]})
		# Check children recursively
		incomplete.extend(_get_incomplete_subtasks(subtask["name"]))

	return incomplete


def _parse_filter_values(value):
	"""Normalize filters coming from query string / list."""
	if value in (None, "", "__all__"):
		return []

	# Already a list/tuple
	if isinstance(value, list | tuple):
		return [str(v) for v in value if v]

	# Try JSON first
	if isinstance(value, str):
		try:
			parsed = frappe.parse_json(value)
			if isinstance(parsed, list):
				return [str(v) for v in parsed if v]
		# Fall back to comma separated values
		except Exception:
			return [v.strip() for v in value.split(",") if v.strip()]

	return []


def _include_missing_parents(tasks: list, project: str, fields: list[str]) -> list:
	"""
	When filters exclude some parents we still want to return them so the tree structure
	is not broken. This function fetches any missing ancestor tasks for the given project.
	"""
	if not tasks:
		return []

	task_names = {task.name for task in tasks}
	parent_names = {
		task.parent_task for task in tasks if task.parent_task and task.parent_task not in task_names
	}

	while parent_names:
		missing_parents = list(parent_names)
		parent_docs = frappe.get_all(
			"Task",
			filters={"name": ["in", missing_parents], "project": project},
			fields=fields,
		)

		if not parent_docs:
			break

		tasks.extend(parent_docs)
		task_names.update({p.name for p in parent_docs})

		# Look for next level parents
		parent_names = {
			p.parent_task for p in parent_docs if p.parent_task and p.parent_task not in task_names
		}

	return tasks


def _get_document_attachments(doctype: str, docname: str):
	"""Return file attachments for a standard Frappe document."""
	if not docname:
		frappe.throw(_("{0} name is required").format(doctype))

	frappe.has_permission(doctype, "read", docname, throw=True)

	return frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": doctype,
			"attached_to_name": docname,
			"is_folder": 0,
		},
		fields=["name", "file_name", "file_url", "file_type", "file_size", "is_private"],
		order_by="creation desc",
	)


def _delete_document_attachment(doctype: str, file_name: str):
	"""Delete a file attachment from a standard Frappe document."""
	if not file_name:
		frappe.throw(_("File name is required"))

	file_doc = frappe.get_doc("File", file_name)

	if file_doc.attached_to_doctype != doctype:
		frappe.throw(_("Invalid attachment"))

	frappe.has_permission(doctype, "write", file_doc.attached_to_name, throw=True)

	frappe.delete_doc("File", file_name)

	return {"success": True}


@frappe.whitelist()
def get_projects():
	"""
	Get list of projects based on user role:
	- Projects Manager / System Manager: sees all projects (except Cancelled)
	- Projects User: sees only projects where they have tasks assigned or are project members

	Returns projects grouped by status (active vs completed).
	"""
	user = frappe.session.user
	user_roles = frappe.get_roles(user)

	# Check if user has manager role
	is_manager = (
		"Projects Manager" in user_roles or "System Manager" in user_roles or "Administrator" in user_roles
	)

	# Base filters - exclude Cancelled and Template projects
	filters = {"status": ["not in", ["Cancelled", "Template"]]}

	if is_manager:
		# Managers see all non-cancelled projects
		projects = frappe.get_all(
			"Project",
			filters=filters,
			fields=[
				"name",
				"project_name",
				"status",
				"percent_complete",
				"expected_start_date",
				"expected_end_date",
				"priority",
			],
			order_by="status asc, modified desc",
		)
	else:
		# Regular users - get projects where they have tasks or are members

		# 1. Get projects where user has assigned tasks
		projects_with_tasks = frappe.db.sql(
			"""
			SELECT DISTINCT t.project
			FROM `tabTask` t
			WHERE t.project IS NOT NULL
			AND t._assign LIKE %s
		""",
			(f"%{user}%",),
			as_dict=True,
		)

		project_names_from_tasks = [p["project"] for p in projects_with_tasks if p["project"]]

		# 2. Get projects where user is a member (via Project User child table)
		projects_as_member = frappe.db.sql(
			"""
			SELECT DISTINCT pu.parent as project
			FROM `tabProject User` pu
			WHERE pu.user = %s
			AND pu.parenttype = 'Project'
		""",
			(user,),
			as_dict=True,
		)

		project_names_from_membership = [p["project"] for p in projects_as_member if p["project"]]

		# Combine both lists
		all_user_projects = list(set(project_names_from_tasks + project_names_from_membership))

		if not all_user_projects:
			return {"active": [], "completed": [], "is_manager": False}

		# Get project details
		projects = frappe.get_all(
			"Project",
			filters={"name": ["in", all_user_projects], "status": ["not in", ["Cancelled", "Template"]]},
			fields=[
				"name",
				"project_name",
				"status",
				"percent_complete",
				"expected_start_date",
				"expected_end_date",
				"priority",
			],
			order_by="status asc, modified desc",
		)

	# Add task count, user's task count, assigned users count, and next milestone for each project
	for project in projects:
		project["task_count"] = frappe.db.count("Task", {"project": project["name"]})

		# Count user's assigned tasks in this project
		if not is_manager:
			user_tasks = frappe.db.sql(
				"""
				SELECT COUNT(*) as count
				FROM `tabTask`
				WHERE project = %s AND _assign LIKE %s
			""",
				(project["name"], f"%{user}%"),
				as_dict=True,
			)
			project["user_task_count"] = user_tasks[0]["count"] if user_tasks else 0

		# Count unique assigned users in project tasks
		assigned_users_result = frappe.db.sql(
			"""
			SELECT _assign
			FROM `tabTask`
			WHERE project = %s AND _assign IS NOT NULL AND _assign != '[]'
		""",
			(project["name"],),
			as_dict=True,
		)

		unique_users = set()
		for row in assigned_users_result:
			if row.get("_assign"):
				try:
					import json

					users = json.loads(row["_assign"])
					if isinstance(users, list):
						unique_users.update(users)
				except Exception:
					pass
		project["assigned_users_count"] = len(unique_users)

		# Get next milestone (closest future milestone_date)
		next_milestone = frappe.db.sql(
			"""
			SELECT name, milestone_name, milestone_date
			FROM `tabProject Milestone`
			WHERE project = %s
			AND milestone_date >= CURDATE()
			ORDER BY milestone_date ASC
			LIMIT 1
		""",
			(project["name"],),
			as_dict=True,
		)

		if next_milestone:
			project["next_milestone"] = next_milestone[0]["milestone_name"]
			project["next_milestone_date"] = next_milestone[0]["milestone_date"]
			# Calculate days remaining
			from frappe.utils import date_diff, today

			project["days_to_milestone"] = date_diff(next_milestone[0]["milestone_date"], today())
		else:
			project["next_milestone"] = None
			project["next_milestone_date"] = None
			project["days_to_milestone"] = None

	# Separate active and completed projects
	active_projects = [p for p in projects if p["status"] != "Completed"]
	completed_projects = [p for p in projects if p["status"] == "Completed"]

	return {"active": active_projects, "completed": completed_projects, "is_manager": is_manager}


@frappe.whitelist()
def get_project_tasks(
	project: str,
	status: str | None = None,
	priority: str | None = None,
	assignee: str | None = None,
	due_today: int | None = None,
	overdue: int | None = None,
	search: str | None = None,
	apply_default_status_filter: int = 1,
):
	"""
	Get all tasks for a project with hierarchical structure.
	Returns tasks sorted by parent and idx for tree building.
	"""
	if not project:
		frappe.throw(_("Project is required"))

	apply_default_status_filter = cint(apply_default_status_filter)
	due_today = cint(due_today)
	overdue = cint(overdue)

	# Get project details
	project_doc = frappe.get_doc("Project", project)

	fields = [
		"name",
		"subject",
		"status",
		"priority",
		"parent_task",
		"is_group",
		"is_milestone",
		"milestone",
		"exp_start_date",
		"exp_end_date",
		"progress",
		"expected_time",
		"description",
		"_assign",
		"idx",
		"creation",
		"modified",
		"project",
	]

	task_filters = {"project": project}
	or_filters = []

	# Status filter
	status_list = _parse_filter_values(status)
	if status is not None:
		if status_list:
			task_filters["status"] = ["in", status_list]
		elif not apply_default_status_filter:
			# Explicit request to avoid default filter -> no status filter
			pass
	if "status" not in task_filters and apply_default_status_filter:
		task_filters["status"] = ["not in", ["Completed", "Cancelled", "Closed", "Template"]]

	# Priority filter
	priority_list = _parse_filter_values(priority)
	if priority_list:
		task_filters["priority"] = ["in", priority_list]

	# Assignee filter (_assign is stored as JSON text)
	if assignee:
		task_filters["_assign"] = ["like", f"%{assignee}%"]

	# Date filters
	if due_today:
		task_filters["exp_end_date"] = today()
	elif overdue:
		task_filters["exp_end_date"] = ["<", today()]
		# Unless caller specified otherwise, keep excluding closed statuses
		if "status" not in task_filters and apply_default_status_filter:
			task_filters["status"] = ["not in", ["Completed", "Cancelled", "Closed", "Template"]]

	# Search filter
	if search:
		or_filters = [
			["subject", "like", f"%{search}%"],
			["description", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]

	# Get filtered tasks for this project
	tasks = frappe.get_all(
		"Task",
		filters=task_filters,
		or_filters=or_filters,
		fields=fields,
		order_by="parent_task, idx, creation",
	)

	# Keep tree structure by including missing parents
	tasks = _include_missing_parents(tasks, project, fields)

	# Deterministic sort
	tasks = sorted(
		tasks,
		key=lambda t: (
			t.get("parent_task") or "",
			t.get("idx") or 0,
			str(t.get("creation") or ""),
		),
	)

	# Get total hours from timesheets
	total_hours = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(tsd.hours), 0) as total_hours
		FROM `tabTimesheet Detail` tsd
		INNER JOIN `tabTimesheet` ts ON tsd.parent = ts.name
		WHERE tsd.project = %s AND ts.docstatus < 2
	""",
		project,
		as_dict=1,
	)

	# Get estimated hours from tasks
	estimated_hours = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(expected_time), 0) as estimated_hours
		FROM `tabTask`
		WHERE project = %s
	""",
		project,
		as_dict=1,
	)

	# Get customer name if customer is set
	customer_name = None
	if project_doc.customer:
		customer_name = frappe.db.get_value("Customer", project_doc.customer, "customer_name")

	# Determine if current user is a manager of this project
	current_user = frappe.session.user
	user_roles = frappe.get_roles(current_user)
	is_role_manager = (
		"Projects Manager" in user_roles or "System Manager" in user_roles or "Administrator" in user_roles
	)
	project_manager_field = getattr(project_doc, "project_manager", None)
	is_project_manager = bool(project_manager_field and project_manager_field == current_user)
	is_manager = is_role_manager or is_project_manager

	return {
		"project": {
			"name": project_doc.name,
			"project_name": project_doc.project_name,
			"status": project_doc.status,
			"project_manager": project_manager_field,
			"percent_complete": project_doc.percent_complete,
			"expected_start_date": project_doc.expected_start_date,
			"expected_end_date": project_doc.expected_end_date,
			"actual_start_date": getattr(project_doc, "actual_start_date", None),
			"actual_end_date": getattr(project_doc, "actual_end_date", None),
			"customer": project_doc.customer,
			"customer_name": customer_name,
			"notes": getattr(project_doc, "notes", None),
			"documentation_url": getattr(project_doc, "documentation_url", None),
			"total_hours": total_hours[0].get("total_hours", 0) if total_hours else 0,
			"estimated_hours": estimated_hours[0].get("estimated_hours", 0) if estimated_hours else 0,
			"is_manager": is_manager,
		},
		"tasks": tasks,
	}


@frappe.whitelist()
def get_project_financials(project: str):
	"""Return financial KPIs and hours breakdown for a project.

	Access is restricted to the project manager (project_manager field == session user)
	or users with System Manager / Projects Manager / Administrator role.
	"""
	if not project:
		frappe.throw(_("Project is required"))

	current_user = frappe.session.user
	user_roles = frappe.get_roles(current_user)
	is_role_manager = (
		"Projects Manager" in user_roles or "System Manager" in user_roles or "Administrator" in user_roles
	)

	project_doc = frappe.get_doc("Project", project)
	project_manager_field = getattr(project_doc, "project_manager", None)
	is_project_manager = bool(project_manager_field and project_manager_field == current_user)

	if not is_role_manager and not is_project_manager:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	# ── Hours breakdown per employee ─────────────────────────────────────────
	hours_by_user = frappe.db.sql(
		"""
		SELECT
			ts.owner AS user_email,
			COALESCE(MAX(ts.employee_name), u.full_name, ts.owner) AS employee_name,
			COALESCE(SUM(CASE WHEN ts.docstatus = 1 THEN tsd.hours ELSE 0 END), 0) AS submitted_hours,
			COALESCE(SUM(CASE WHEN ts.docstatus = 0 THEN tsd.hours ELSE 0 END), 0) AS draft_hours,
			COALESCE(SUM(tsd.hours), 0) AS total_hours
		FROM `tabTimesheet Detail` tsd
		INNER JOIN `tabTimesheet` ts ON tsd.parent = ts.name
		LEFT JOIN `tabUser` u ON ts.owner = u.name
		WHERE tsd.project = %s AND ts.docstatus < 2
		GROUP BY ts.owner
		ORDER BY total_hours DESC
		""",
		project,
		as_dict=True,
	)

	submitted_hours = 0.0
	draft_hours = 0.0
	hours_per_user = []
	for row in hours_by_user:
		s = float(row["submitted_hours"])
		d = float(row["draft_hours"])
		submitted_hours += s
		draft_hours += d
		label = row["employee_name"] or row["user_email"] or "Unknown"
		hours_per_user.append(
			{
				"user": row["user_email"] or label,
				"label": label,
				"submitted": round(s, 2),
				"draft": round(d, 2),
				"total": round(s + d, 2),
			}
		)

	# ── Estimated hours ───────────────────────────────────────────────────────
	estimated_hours_result = frappe.db.sql(
		"SELECT COALESCE(SUM(expected_time), 0) FROM `tabTask` WHERE project = %s",
		project,
	)
	estimated_hours = float((estimated_hours_result[0][0] if estimated_hours_result else 0) or 0)

	# ── Financial fields from Project doc ─────────────────────────────────────
	estimated_costing = float(getattr(project_doc, "estimated_costing", 0) or 0)
	total_costing_amount = float(getattr(project_doc, "total_costing_amount", 0) or 0)
	total_purchase_cost = float(getattr(project_doc, "total_purchase_cost", 0) or 0)
	total_consumed_material_cost = float(getattr(project_doc, "total_consumed_material_cost", 0) or 0)
	gross_margin = float(getattr(project_doc, "gross_margin", 0) or 0)
	per_gross_margin = float(getattr(project_doc, "per_gross_margin", 0) or 0)
	total_sales_amount = float(getattr(project_doc, "total_sales_amount", 0) or 0)

	# ── Budget margin ─────────────────────────────────────────────────────────
	total_current_cost = total_costing_amount + total_purchase_cost + total_consumed_material_cost
	budget_margin = (estimated_costing - total_current_cost) if estimated_costing > 0 else 0.0
	per_budget_margin = (budget_margin / estimated_costing * 100) if estimated_costing > 0 else 0.0

	# ── Simple cost estimate based on hours ──────────────────────────────────
	total_reported_hours = round(submitted_hours + draft_hours, 2)

	return {
		"estimated_costing": estimated_costing,
		"total_costing_amount": total_costing_amount,
		"total_purchase_cost": total_purchase_cost,
		"total_consumed_material_cost": round(total_consumed_material_cost, 2),
		"total_current_cost": round(total_current_cost, 2),
		"budget_margin": round(budget_margin, 2),
		"per_budget_margin": round(per_budget_margin, 2),
		"gross_margin": gross_margin,
		"per_gross_margin": per_gross_margin,
		"total_sales_amount": total_sales_amount,
		"estimated_hours": estimated_hours,
		"total_hours": total_reported_hours,
		"submitted_hours": round(submitted_hours, 2),
		"draft_hours": round(draft_hours, 2),
		"hours_per_user": hours_per_user,
	}


@frappe.whitelist()
def update_project(
	project: str,
	expected_start_date: str | None = None,
	expected_end_date: str | None = None,
	documentation_url: str | None = None,
):
	if not project:
		frappe.throw(_("Project is required"))

	project_doc = frappe.get_doc("Project", project)

	if not frappe.has_permission("Project", "write", doc=project_doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	documentation_url_provided = documentation_url is not None

	if expected_start_date == "":
		expected_start_date = None
	if expected_end_date == "":
		expected_end_date = None
	if documentation_url == "":
		documentation_url = None

	# Update fields directly in database to avoid triggering notifications
	if expected_start_date is not None:
		frappe.db.set_value("Project", project, "expected_start_date", expected_start_date)
	if expected_end_date is not None:
		frappe.db.set_value("Project", project, "expected_end_date", expected_end_date)
	if documentation_url_provided and frappe.get_meta("Project").has_field("documentation_url"):
		frappe.db.set_value("Project", project, "documentation_url", documentation_url)

	# Get updated project data
	project_doc.reload()

	total_hours = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(tsd.hours), 0) as total_hours
		FROM `tabTimesheet Detail` tsd
		INNER JOIN `tabTimesheet` ts ON tsd.parent = ts.name
		WHERE tsd.project = %s AND ts.docstatus < 2
	""",
		project,
		as_dict=1,
	)

	estimated_hours = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(expected_time), 0) as estimated_hours
		FROM `tabTask`
		WHERE project = %s
	""",
		project,
		as_dict=1,
	)

	customer_name = None
	if project_doc.customer:
		customer_name = frappe.db.get_value("Customer", project_doc.customer, "customer_name")

	return {
		"name": project_doc.name,
		"project_name": project_doc.project_name,
		"status": project_doc.status,
		"project_manager": getattr(project_doc, "project_manager", None),
		"percent_complete": project_doc.percent_complete,
		"expected_start_date": project_doc.expected_start_date,
		"expected_end_date": project_doc.expected_end_date,
		"actual_start_date": getattr(project_doc, "actual_start_date", None),
		"actual_end_date": getattr(project_doc, "actual_end_date", None),
		"customer": project_doc.customer,
		"customer_name": customer_name,
		"notes": getattr(project_doc, "notes", None),
		"documentation_url": getattr(project_doc, "documentation_url", None),
		"total_hours": total_hours[0].get("total_hours", 0) if total_hours else 0,
		"estimated_hours": estimated_hours[0].get("estimated_hours", 0) if estimated_hours else 0,
	}


@frappe.whitelist()
def create_task(
	subject: str,
	project: str,
	parent_task: str | None = None,
	priority: str = "Medium",
	status: str = "Open",
	exp_end_date: str | None = None,
):
	"""Create a new task."""
	if not subject or not project:
		frappe.throw(_("Subject and Project are required"))

	# If parent_task is provided, ensure it's a group task
	if parent_task:
		parent = frappe.get_doc("Task", parent_task)
		if not parent.is_group:
			# Automatically make it a group
			parent.is_group = 1
			parent.save()

	# Calculate idx (position in list)
	existing_tasks = frappe.get_all(
		"Task",
		filters={"project": project, "parent_task": parent_task or ["is", "not set"]},
		fields=["idx"],
		order_by="idx desc",
		limit=1,
	)
	new_idx = (existing_tasks[0]["idx"] + 1) if existing_tasks else 0

	task = frappe.get_doc(
		{
			"doctype": "Task",
			"subject": subject,
			"project": project,
			"parent_task": parent_task,
			"priority": priority,
			"status": status,
			"exp_end_date": exp_end_date,
			"idx": new_idx,
		}
	)
	task.insert()

	return {
		"name": task.name,
		"subject": task.subject,
		"status": task.status,
		"priority": task.priority,
		"parent_task": task.parent_task,
		"is_group": task.is_group,
		"exp_start_date": task.exp_start_date,
		"exp_end_date": task.exp_end_date,
		"progress": task.progress,
		"idx": task.idx,
	}


@frappe.whitelist()
def update_task(task_name: str, **kwargs):
	"""Update task fields."""
	if not task_name:
		frappe.throw(_("Task name is required"))

	task = frappe.get_doc("Task", task_name)

	# Check if trying to set status to Completed
	if kwargs.get("status") == "Completed":
		incomplete_subtasks = _get_incomplete_subtasks(task_name)
		if incomplete_subtasks:
			subtask_names = ", ".join([s["subject"] for s in incomplete_subtasks[:3]])
			if len(incomplete_subtasks) > 3:
				subtask_names += f" and {len(incomplete_subtasks) - 3} more"

			# Show as info message instead of error
			frappe.msgprint(
				_("Cannot complete task. {0} subtask(s) are not completed: {1}").format(
					len(incomplete_subtasks), subtask_names
				),
				title=_("Complete Subtasks First"),
				indicator="blue",
			)
			# Return current task state without changes
			return {
				"name": task.name,
				"subject": task.subject,
				"status": task.status,
				"priority": task.priority,
				"parent_task": task.parent_task,
				"is_group": task.is_group,
				"exp_start_date": task.exp_start_date,
				"exp_end_date": task.exp_end_date,
				"progress": task.progress,
				"description": task.description,
			}

	# Allowed fields to update
	allowed_fields = [
		"subject",
		"status",
		"priority",
		"exp_start_date",
		"exp_end_date",
		"progress",
		"description",
		"is_group",
		"project",
		"expected_time",
	]

	for field in allowed_fields:
		if field not in kwargs:
			continue
		task.set(field, kwargs[field])

	# Set completed_on date when task is completed, clear it otherwise
	if kwargs.get("status") == "Completed":
		task.completed_on = today()
	elif "status" in kwargs and kwargs["status"] != "Completed":
		task.completed_on = None

	task.save()

	result = {
		"name": task.name,
		"subject": task.subject,
		"status": task.status,
		"priority": task.priority,
		"parent_task": task.parent_task,
		"is_group": task.is_group,
		"exp_start_date": task.exp_start_date,
		"exp_end_date": task.exp_end_date,
		"progress": task.progress,
		"description": task.description,
		"project": task.project,
		"expected_time": getattr(task, "expected_time", None),
		"completed_on": task.completed_on,
	}

	# Publish only to users linked with this project (plus current user) to avoid
	# leaking task payloads to all Desk users.
	project_users = frappe.get_all(
		"Project User",
		filters={"parent": task.project, "parenttype": "Project"},
		pluck="user",
	)
	allowed_users = {u for u in project_users if u}
	if frappe.session.user and frappe.session.user != "Guest":
		allowed_users.add(frappe.session.user)

	for user in allowed_users:
		frappe.publish_realtime(
			"projekt_hub_task_updated",
			{"project": task.project, "task": result},
			user=user,
			after_commit=True,
		)

	return result


@frappe.whitelist()
def get_all_projects():
	"""
	Get list of all active projects for task project change dropdown.
	Returns only non-cancelled and non-template projects.
	"""
	projects = frappe.get_all(
		"Project",
		filters={"status": ["not in", ["Cancelled", "Template"]]},
		fields=["name", "project_name", "status"],
		order_by="project_name asc",
	)
	return projects


@frappe.whitelist()
def delete_task(task_name: str):
	"""Delete a task and optionally its children."""
	if not task_name:
		frappe.throw(_("Task name is required"))

	# Check for children
	children = frappe.get_all("Task", filters={"parent_task": task_name})

	if children:
		# Delete children first (recursive)
		for child in children:
			delete_task(child["name"])

	frappe.delete_doc("Task", task_name)

	return {"success": True}


@frappe.whitelist()
def reorder_task(
	task_name: str,
	parent_task: str | None = None,
	idx: int = 0,
):
	"""
	Reorder a task - change its parent and/or position.
	This handles both reparenting and reordering within the same parent.
	"""
	if not task_name:
		frappe.throw(_("Task name is required"))

	task = frappe.get_doc("Task", task_name)
	old_parent = task.parent_task

	# If changing parent
	if parent_task != old_parent:
		# If new parent exists, ensure it's a group
		if parent_task:
			new_parent = frappe.get_doc("Task", parent_task)
			if not new_parent.is_group:
				new_parent.is_group = 1
				new_parent.save()

		task.parent_task = parent_task

	# Update idx
	task.idx = idx
	task.flags.ignore_recursion_check = True
	task.save()

	# Reindex siblings to maintain order
	siblings = frappe.get_all(
		"Task",
		filters={
			"project": task.project,
			"parent_task": parent_task or ["is", "not set"],
			"name": ["!=", task_name],
		},
		fields=["name", "idx"],
		order_by="idx",
	)

	# Adjust indices
	for i, sibling in enumerate(siblings):
		new_idx = i if i < idx else i + 1
		if sibling["idx"] != new_idx:
			frappe.db.set_value("Task", sibling["name"], "idx", new_idx)

	return {"success": True}


@frappe.whitelist()
def toggle_task_status(task_name: str):
	"""Toggle task between Open and Completed."""
	if not task_name:
		frappe.throw(_("Task name is required"))

	task = frappe.get_doc("Task", task_name)

	if task.status == "Completed":
		task.status = "Open"
		task.progress = 0
	else:
		# Check for incomplete subtasks before completing
		incomplete_subtasks = _get_incomplete_subtasks(task_name)
		if incomplete_subtasks:
			subtask_names = ", ".join([s["subject"] for s in incomplete_subtasks[:3]])
			if len(incomplete_subtasks) > 3:
				subtask_names += f" and {len(incomplete_subtasks) - 3} more"

			# Show as info message instead of error
			frappe.msgprint(
				_("Cannot complete task. {0} subtask(s) are not completed: {1}").format(
					len(incomplete_subtasks), subtask_names
				),
				title=_("Complete Subtasks First"),
				indicator="blue",
			)
			# Return current task state without changes
			return {
				"name": task.name,
				"status": task.status,
				"progress": task.progress,
			}
		task.status = "Completed"
		task.progress = 100

	task.save()

	return {
		"name": task.name,
		"status": task.status,
		"progress": task.progress,
	}


@frappe.whitelist()
def bulk_update_tasks(tasks: list):
	"""
	Bulk update multiple tasks at once.
	Useful for drag & drop reordering.
	"""
	if not tasks:
		return {"success": True}

	if isinstance(tasks, str):
		import json

		tasks = json.loads(tasks)

	for task_data in tasks:
		task_name = task_data.get("name")
		if not task_name:
			continue

		frappe.db.set_value(
			"Task",
			task_name,
			{
				"parent_task": task_data.get("parent_task"),
				"idx": task_data.get("idx", 0),
			},
		)

	return {"success": True}


@frappe.whitelist()
def get_users():
	"""Get list of users that can be assigned to tasks (only users with an active Employee record)."""
	employee_user_ids = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		pluck="user_id",
	)
	# Remove empty/None values
	employee_user_ids = [uid for uid in employee_user_ids if uid]

	if not employee_user_ids:
		return []

	users = frappe.get_all(
		"User",
		filters={
			"enabled": 1,
			"name": ["in", employee_user_ids],
		},
		fields=["name", "full_name", "user_image"],
		order_by="full_name",
	)
	return users


@frappe.whitelist()
def assign_task(
	task_name: str,
	user: str | None = None,
	action: str = "add",
):
	"""Assign or unassign a user to/from a task."""
	if not task_name:
		frappe.throw(_("Task name is required"))

	from frappe.desk.form.assign_to import add as add_assignment
	from frappe.desk.form.assign_to import remove as remove_assignment

	if action == "add" and user:
		add_assignment(
			{
				"doctype": "Task",
				"name": task_name,
				"assign_to": [user],
			}
		)

		# Auto-assign user to project if not already assigned
		task = frappe.get_doc("Task", task_name)
		if task.project:
			# Check if user is already assigned to the project
			existing = frappe.db.exists("Project User", {"parent": task.project, "user": user})

			if not existing:
				# Add user to project
				try:
					project_user = frappe.get_doc(
						{
							"doctype": "Project User",
							"parent": task.project,
							"parenttype": "Project",
							"parentfield": "users",
							"user": user,
						}
					)
					project_user.insert(ignore_permissions=True)
				except Exception as e:
					frappe.log_error(f"Failed to auto-assign user {user} to project {task.project}: {e!s}")

	elif action == "remove" and user:
		remove_assignment("Task", task_name, user)
	elif action == "clear":
		# Remove all assignments
		assignments = frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "Task",
				"reference_name": task_name,
				"status": "Open",
			},
			pluck="allocated_to",
		)
		for assigned_user in assignments:
			remove_assignment("Task", task_name, assigned_user)

	# Get updated task with _assign
	task = frappe.get_doc("Task", task_name)

	return {
		"name": task.name,
		"_assign": task._assign,
	}


@frappe.whitelist()
def get_project_users(project: str):
	"""Get users assigned to a project."""
	if not project:
		frappe.throw(_("Project is required"))

	project_doc = frappe.get_doc("Project", project)

	users = []
	for user in project_doc.users:
		user_doc = frappe.get_doc("User", user.user)
		users.append(
			{
				"user": user.user,
				"full_name": user_doc.full_name,
				"user_image": user_doc.user_image,
			}
		)

	return users


@frappe.whitelist()
def add_project_user(project: str, user: str):
	"""Add a user to a project."""
	if not project or not user:
		frappe.throw(_("Project and user are required"))

	# Check if user already exists
	existing = frappe.db.exists("Project User", {"parent": project, "user": user})

	if existing:
		return {"message": "User already in project"}

	# Insert directly into child table to avoid email notifications
	project_user = frappe.get_doc(
		{
			"doctype": "Project User",
			"parent": project,
			"parenttype": "Project",
			"parentfield": "users",
			"user": user,
		}
	)
	project_user.insert(ignore_permissions=True)

	return {"success": True}


@frappe.whitelist()
def remove_project_user(project: str, user: str):
	"""Remove a user from a project."""
	if not project or not user:
		frappe.throw(_("Project and user are required"))

	# Delete directly from child table to avoid email notifications
	frappe.db.delete("Project User", {"parent": project, "user": user})

	return {"success": True}


@frappe.whitelist()
def get_task_timelogs(task_name: str):
	"""Get all time logs for a specific task."""
	if not task_name:
		frappe.throw(_("Task name is required"))

	# Get timesheets that have time logs for this task
	timelogs = frappe.db.sql(
		"""
		SELECT
			ts.name as timesheet_name,
			ts.owner,
			ts.status,
			tsd.name as timelog_name,
			tsd.activity_type,
			tsd.hours,
			tsd.is_billable,
			tsd.from_time,
			tsd.to_time,
			tsd.description,
			tsd.idx,
			ts.creation,
			ts.modified
		FROM `tabTimesheet Detail` tsd
		INNER JOIN `tabTimesheet` ts ON tsd.parent = ts.name
		WHERE tsd.task = %s
		ORDER BY tsd.from_time DESC
		""",
		task_name,
		as_dict=1,
	)

	# Get user details for each log
	for log in timelogs:
		user = frappe.get_cached_doc("User", log.owner)
		log["user_full_name"] = user.full_name
		log["user_image"] = user.user_image

	# Calculate total hours
	total_hours = sum(log.get("hours", 0) for log in timelogs)

	return {
		"timelogs": timelogs,
		"total_hours": total_hours,
	}


@frappe.whitelist()
def get_my_timelogs(
	start_date: str | None = None,
	end_date: str | None = None,
	status: str | None = None,
	project: str | None = None,
	activity_type: str | None = None,
	search: str | None = None,
):
	"""Get time logs for the current user with optional filters."""
	user = frappe.session.user

	conditions = ["ts.owner = %s", "ts.docstatus < 2"]
	values: list[str] = [user]

	if status:
		conditions.append("ts.status = %s")
		values.append(status)
	if project:
		conditions.append("tsd.project = %s")
		values.append(project)
	if activity_type:
		conditions.append("tsd.activity_type = %s")
		values.append(activity_type)
	if start_date:
		conditions.append("DATE(tsd.from_time) >= %s")
		values.append(start_date)
	if end_date:
		conditions.append("DATE(tsd.from_time) <= %s")
		values.append(end_date)
	if search:
		search_value = f"%{search}%"
		conditions.append(
			"(tsd.description LIKE %s OR tsd.task LIKE %s OR task.subject LIKE %s OR tsd.project LIKE %s)"
		)
		values.extend([search_value, search_value, search_value, search_value])

	condition_sql = " AND ".join(conditions)

	query = (
		"""
		SELECT
			ts.name as timesheet_name,
			ts.status,
			ts.docstatus,
			ts.owner,
			tsd.name as timelog_name,
			tsd.activity_type,
			tsd.hours,
			tsd.is_billable,
			tsd.from_time,
			tsd.to_time,
			tsd.description,
			tsd.task,
			tsd.project,
			tsd.idx,
			ts.creation,
			ts.modified,
			task.subject as task_subject,
			proj.project_name as project_name
		FROM `tabTimesheet Detail` tsd
		INNER JOIN `tabTimesheet` ts ON tsd.parent = ts.name
		LEFT JOIN `tabTask` task ON tsd.task = task.name
		LEFT JOIN `tabProject` proj ON tsd.project = proj.name
		WHERE """
		+ condition_sql
		+ """
		ORDER BY tsd.from_time DESC, tsd.idx DESC
		"""
	)
	timelogs = frappe.db.sql(query, values, as_dict=1)

	return {"timelogs": timelogs, "total": len(timelogs)}


@frappe.whitelist()
def get_all_timelogs(
	start_date: str | None = None,
	end_date: str | None = None,
	status: str | None = None,
	project: str | None = None,
	activity_type: str | None = None,
	search: str | None = None,
	employee: str | None = None,
):
	"""Get time logs for all users (manager only)."""
	user_roles = frappe.get_roles(frappe.session.user)
	is_manager = (
		"Projects Manager" in user_roles
		or "Project Manager" in user_roles
		or "System Manager" in user_roles
		or "Administrator" in user_roles
	)
	if not is_manager:
		frappe.throw(_("You do not have permission to view all time logs"), frappe.PermissionError)

	conditions = ["ts.docstatus < 2"]
	values: list = []

	if employee:
		conditions.append("ts.owner = %s")
		values.append(employee)
	if status:
		conditions.append("ts.status = %s")
		values.append(status)
	if project:
		conditions.append("tsd.project = %s")
		values.append(project)
	if activity_type:
		conditions.append("tsd.activity_type = %s")
		values.append(activity_type)
	if start_date:
		conditions.append("DATE(tsd.from_time) >= %s")
		values.append(start_date)
	if end_date:
		conditions.append("DATE(tsd.from_time) <= %s")
		values.append(end_date)
	if search:
		search_value = f"%{search}%"
		conditions.append(
			"(tsd.description LIKE %s OR tsd.task LIKE %s OR task.subject LIKE %s OR tsd.project LIKE %s OR ts.owner LIKE %s)"
		)
		values.extend([search_value] * 5)

	condition_sql = " AND ".join(conditions)
	query = (
		"""
		SELECT
			ts.name as timesheet_name,
			ts.status,
			ts.docstatus,
			ts.owner,
			tsd.name as timelog_name,
			tsd.activity_type,
			tsd.hours,
			tsd.is_billable,
			tsd.from_time,
			tsd.to_time,
			tsd.description,
			tsd.task,
			tsd.project,
			tsd.idx,
			ts.creation,
			ts.modified,
			task.subject as task_subject,
			proj.project_name as project_name,
			u.full_name as owner_full_name
		FROM `tabTimesheet Detail` tsd
		INNER JOIN `tabTimesheet` ts ON tsd.parent = ts.name
		LEFT JOIN `tabTask` task ON tsd.task = task.name
		LEFT JOIN `tabProject` proj ON tsd.project = proj.name
		LEFT JOIN `tabUser` u ON ts.owner = u.name
		WHERE """
		+ condition_sql
		+ """
		ORDER BY tsd.from_time DESC, tsd.idx DESC
		"""
	)
	timelogs = frappe.db.sql(query, values, as_dict=1)
	return {"timelogs": timelogs, "total": len(timelogs)}


@frappe.whitelist()
def get_all_users_with_timelogs():
	"""Get list of users who have timesheets (manager only)."""
	user_roles = frappe.get_roles(frappe.session.user)
	is_manager = (
		"Projects Manager" in user_roles
		or "Project Manager" in user_roles
		or "System Manager" in user_roles
		or "Administrator" in user_roles
	)
	if not is_manager:
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	users = frappe.db.sql(
		"""
		SELECT DISTINCT ts.owner as user, u.full_name
		FROM `tabTimesheet` ts
		JOIN `tabUser` u ON ts.owner = u.name
		ORDER BY u.full_name
		""",
		as_dict=True,
	)
	return users


@frappe.whitelist()
def create_timelog(
	task: str,
	hours: float,
	activity_type: str | None = "Execution",
	description: str | None = None,
	from_time: str | None = None,
	to_time: str | None = None,
	is_billable: int | None = None,
):
	"""
	Create a time log entry for a task.
	Creates or updates a timesheet for the current user.
	"""
	if not task or not hours:
		frappe.throw(_("Task and hours are required"))

	# Validate hours
	try:
		hours = float(hours)
		if hours <= 0:
			frappe.throw(_("Hours must be greater than 0"))
	except ValueError:
		frappe.throw(_("Invalid hours value"))

	# Get or create timesheet for current user
	user = frappe.session.user
	today = frappe.utils.today()

	# Try to find an existing draft timesheet for today
	existing_timesheet = frappe.get_all(
		"Timesheet",
		filters={
			"owner": user,
			"docstatus": 0,  # Draft
			"start_date": ["<=", today],
			"end_date": [">=", today],
		},
		limit=1,
	)

	# Get task details
	task_doc = frappe.get_doc("Task", task)
	timelog_meta = frappe.get_meta("Timesheet Detail")

	timelog_row = {
		"activity_type": activity_type,
		"hours": hours,
		"from_time": from_time or frappe.utils.now(),
		"to_time": to_time or frappe.utils.now(),
		"description": description or "",
		"task": task,
		"project": task_doc.project,
	}
	if is_billable is not None and timelog_meta.has_field("is_billable"):
		timelog_row["is_billable"] = cint(is_billable)

	if existing_timesheet:
		timesheet = frappe.get_doc("Timesheet", existing_timesheet[0].name)
		# Add time log detail to existing timesheet
		timesheet.append("time_logs", timelog_row)
		timesheet.save()
	else:
		# Create new timesheet with time log in one go
		timesheet = frappe.get_doc(
			{
				"doctype": "Timesheet",
				"employee": get_employee_for_user(user),
				"start_date": today,
				"end_date": today,
				"time_logs": [timelog_row],
			}
		)
		timesheet.insert()

	# Return the created log with user info
	latest_log = timesheet.time_logs[-1]

	# Get user details
	user_doc = frappe.get_cached_doc("User", user)

	return {
		"timesheet_name": timesheet.name,
		"timelog_name": latest_log.name,
		"activity_type": latest_log.activity_type,
		"hours": latest_log.hours,
		"is_billable": getattr(latest_log, "is_billable", 0),
		"from_time": latest_log.from_time,
		"to_time": latest_log.to_time,
		"description": latest_log.description,
		"task": latest_log.task,
		"project": latest_log.project,
		"status": timesheet.status,
		"owner": user,
		"user_full_name": user_doc.full_name,
		"user_image": user_doc.user_image,
	}


@frappe.whitelist()
def update_timelog(
	timelog_name: str,
	hours: float | None = None,
	activity_type: str | None = None,
	description: str | None = None,
	from_time: str | None = None,
	to_time: str | None = None,
	project: str | None = None,
	is_billable: int | None = None,
):
	"""Update an existing time log entry."""
	if not timelog_name:
		frappe.throw(_("Timelog name is required"))

	# Get the timesheet detail
	timelog = frappe.get_doc("Timesheet Detail", timelog_name)
	timesheet = frappe.get_doc("Timesheet", timelog.parent)

	# Check if user owns this timesheet
	if timesheet.owner != frappe.session.user:
		frappe.throw(_("You can only edit your own time logs"))

	# Validate timesheet state before update
	if timesheet.docstatus == 1:
		frappe.throw(_("Cannot update time logs from a submitted timesheet. Please cancel it first."))
	elif timesheet.docstatus == 2:
		frappe.throw(_("Cannot modify a cancelled timesheet"))

	# Update fields
	if hours is not None:
		timelog.hours = float(hours)
	if activity_type:
		timelog.activity_type = activity_type
	if description is not None:
		timelog.description = description
	if from_time:
		timelog.from_time = from_time
	if to_time:
		timelog.to_time = to_time
	if project is not None:
		if project:
			if not frappe.db.exists("Project", project):
				frappe.throw(_("Project {0} does not exist").format(project))
			project_status = frappe.db.get_value("Project", project, "status")
			if project_status == "Cancelled":
				frappe.throw(_("Cannot assign to a cancelled project"))
		timelog.project = project
	if is_billable is not None and timelog.meta.has_field("is_billable"):
		timelog.is_billable = cint(is_billable)

	timesheet.save()

	return {
		"timelog_name": timelog.name,
		"hours": timelog.hours,
		"activity_type": timelog.activity_type,
		"description": timelog.description,
		"project": timelog.project,
		"is_billable": getattr(timelog, "is_billable", 0),
	}


@frappe.whitelist()
def delete_timelog(timelog_name: str):
	"""Delete a time log entry."""
	if not timelog_name:
		frappe.throw(_("Timelog name is required"))

	# Get the timesheet detail
	timelog = frappe.get_doc("Timesheet Detail", timelog_name)
	timesheet = frappe.get_doc("Timesheet", timelog.parent)

	# Check if user owns this timesheet or has admin privileges
	is_admin_deletion = False
	if timesheet.owner != frappe.session.user:
		# Allow System Manager and Administrator roles to delete any time logs
		user_roles = frappe.get_roles(frappe.session.user)
		if "System Manager" not in user_roles and "Administrator" not in user_roles:
			frappe.throw(_("You can only delete your own time logs"))
		else:
			is_admin_deletion = True

	# Validate timesheet state before deletion
	if timesheet.docstatus == 1:
		frappe.throw(_("Cannot delete time logs from a submitted timesheet. Please cancel it first."))
	elif timesheet.docstatus == 2:
		frappe.throw(_("Cannot modify a cancelled timesheet"))

	# Check for linked documents before attempting deletion
	linked_docs = frappe.get_all(
		"Dynamic Link",
		filters={"link_doctype": "Timesheet", "link_name": timesheet.name},
		fields=["parent", "parenttype"],
	)

	if linked_docs:
		doc_list = ", ".join([f"{doc['parenttype']}: {doc['parent']}" for doc in linked_docs])
		frappe.throw(_("Cannot delete timesheet. It is linked to: {0}").format(doc_list))

	# Reload to prevent race condition before checking
	timesheet.reload()

	# Find the time log to remove (after reload)
	row = None
	for d in timesheet.time_logs:
		if d.name == timelog_name:
			row = d
			break

	# If row is already gone, treat as success (idempotent)
	if not row:
		return {"success": True}

	# Check if this is the last time log before removing
	if len(timesheet.time_logs) == 1:
		# If this is the last time log, delete the entire timesheet
		frappe.delete_doc("Timesheet", timesheet.name)
	else:
		# Otherwise, just remove this time log and save
		timesheet.remove(row)
		timesheet.save()

	# Log administrative deletion for audit trail
	if is_admin_deletion:
		frappe.log_error(
			f"Admin User {frappe.session.user} deleted time log '{timelog_name}' from timesheet '{timesheet.name}' owned by '{timesheet.owner}'",
			"Administrative Timesheet Deletion",
		)

	return {"success": True}


def get_employee_for_user(user: str):
	"""Get employee linked to user, or None if not found."""
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	return employee


@frappe.whitelist()
def get_activity_types():
	"""Get list of activity types from ERPNext."""
	activity_types = frappe.get_all(
		"Activity Type",
		filters={"disabled": 0},
		fields=["name", "activity_type"],
		order_by="name",
	)
	# Return just the names as a list
	return [at.get("activity_type") or at.get("name") for at in activity_types]


@frappe.whitelist()
def get_task_statuses():
	"""Get list of task statuses from ERPNext."""
	# Get status options from Task doctype meta
	task_meta = frappe.get_meta("Task")
	status_field = task_meta.get_field("status")

	if status_field and status_field.options:
		# Options are stored as newline-separated string
		statuses = [s.strip() for s in status_field.options.split("\n") if s.strip()]
		return statuses

	# Fallback to default statuses
	return ["Open", "Working", "Pending Review", "Completed", "Overdue", "Cancelled"]


@frappe.whitelist()
def get_task_priorities():
	"""Get list of task priorities from ERPNext."""
	# Get priority options from Task doctype meta
	task_meta = frappe.get_meta("Task")
	priority_field = task_meta.get_field("priority")

	if priority_field and priority_field.options:
		# Options are stored as newline-separated string
		priorities = [p.strip() for p in priority_field.options.split("\n") if p.strip()]
		return priorities

	# Fallback to default priorities
	return ["Low", "Medium", "High", "Urgent"]


# =============================================================================
# MILESTONE API
# =============================================================================


@frappe.whitelist()
def get_project_milestones(project: str):
	"""
	Get all milestones for a project with calculated progress and health status.
	Milestones are always scoped to a single project.
	"""
	if not project:
		frappe.throw(_("Project is required"))

	milestones = frappe.get_all(
		"Project Milestone",
		filters={"project": project},
		fields=[
			"name",
			"milestone_name",
			"description",
			"milestone_date",
			"status",
			"priority",
			"color",
			"progress",
			"total_tasks",
			"completed_tasks",
			"sort_order",
		],
		order_by="sort_order asc, milestone_date asc, creation asc",
	)

	for milestone in milestones:
		milestone["health"] = _calculate_milestone_health(milestone)

	return milestones


@frappe.whitelist()
def reorder_milestones(project: str, milestone_names: list | str):
	"""Persist manual sort order for milestones of a project."""
	if not project:
		frappe.throw(_("Project is required"))

	# ── Permission check ─────────────────────────────────────────────────────
	current_user = frappe.session.user
	user_roles = frappe.get_roles(current_user)
	is_admin = (
		"System Manager" in user_roles or "Administrator" in user_roles or "Projects Manager" in user_roles
	)

	# Get project doc to verify access
	project_doc = frappe.get_doc("Project", project)
	is_project_manager = project_doc.project_manager == current_user
	is_team_member = current_user in [m.user for m in (project_doc.team or [])]

	if not (is_admin or is_project_manager or is_team_member):
		frappe.throw(_("You do not have permission to reorder milestones"), frappe.PermissionError)

	# ── Validate milestones belong to project ────────────────────────────────
	if isinstance(milestone_names, str):
		import json as _json

		milestone_names = _json.loads(milestone_names)

	# Get all milestones for this project
	valid_milestone_names = set(
		frappe.db.get_list(
			"Project Milestone",
			filters={"project": project},
			fields=["name"],
			pluck="name",
		)
	)

	# Verify all provided milestone names belong to this project
	for name in milestone_names:
		if name not in valid_milestone_names:
			frappe.throw(
				_("Milestone {0} does not belong to project {1}").format(name, project),
				frappe.ValidationError,
			)

	# ── Update sort order ────────────────────────────────────────────────────
	for idx, name in enumerate(milestone_names):
		frappe.db.set_value("Project Milestone", name, "sort_order", idx, update_modified=False)

	frappe.db.commit()
	return {"success": True}


def _calculate_milestone_health(milestone):
	"""Calculate health status based on deadline and progress."""
	if milestone.get("status") == "Completed":
		return "completed"

	if milestone.get("status") == "Cancelled":
		return "cancelled"

	if not milestone.get("milestone_date"):
		return "no_deadline"

	from frappe.utils import date_diff, getdate, today

	deadline = getdate(milestone["milestone_date"])
	today_date = getdate(today())

	if deadline < today_date:
		return "overdue"

	days_remaining = date_diff(deadline, today_date)
	progress = milestone.get("progress", 0)

	# At risk if less than 7 days and less than 70% done
	if days_remaining <= 7 and progress < 70:
		return "at_risk"

	# At risk if less than 14 days and less than 50% done
	if days_remaining <= 14 and progress < 50:
		return "at_risk"

	return "on_track"


@frappe.whitelist()
def create_milestone(
	project: str,
	milestone_name: str,
	description: str | None = None,
	milestone_date: str | None = None,
	priority: str = "Medium",
	color: str | None = None,
):
	"""
	Create a new milestone for a project.
	Milestone is always linked to exactly one project.
	"""
	if not project:
		frappe.throw(_("Project is required"))

	if not milestone_name:
		frappe.throw(_("Milestone name is required"))

	# Verify project exists
	if not frappe.db.exists("Project", project):
		frappe.throw(_("Project {0} does not exist").format(project))

	milestone = frappe.get_doc(
		{
			"doctype": "Project Milestone",
			"project": project,
			"milestone_name": milestone_name,
			"description": description,
			"milestone_date": milestone_date,
			"priority": priority,
			"color": color,
			"status": "Open",
		}
	)

	milestone.insert()

	return {
		"name": milestone.name,
		"milestone_name": milestone.milestone_name,
		"project": milestone.project,
		"description": milestone.description,
		"milestone_date": milestone.milestone_date,
		"status": milestone.status,
		"priority": milestone.priority,
		"color": milestone.color,
		"progress": milestone.progress,
		"total_tasks": milestone.total_tasks,
		"completed_tasks": milestone.completed_tasks,
		"health": "on_track",
	}


@frappe.whitelist()
def update_milestone(
	milestone_name: str,
	new_milestone_name: str | None = None,
	description: str | None = None,
	milestone_date: str | None = None,
	status: str | None = None,
	priority: str | None = None,
	color: str | None = None,
):
	"""
	Update milestone details.
	Project cannot be changed - milestone is always bound to its original project.
	"""
	if not milestone_name:
		frappe.throw(_("Milestone name is required"))

	milestone = frappe.get_doc("Project Milestone", milestone_name)

	# Update allowed fields
	if new_milestone_name is not None:
		milestone.milestone_name = new_milestone_name

	if description is not None:
		milestone.description = description

	if milestone_date is not None:
		milestone.milestone_date = milestone_date

	if status is not None:
		milestone.status = status

	if priority is not None:
		milestone.priority = priority

	if color is not None:
		milestone.color = color

	milestone.save()

	return {
		"name": milestone.name,
		"milestone_name": milestone.milestone_name,
		"project": milestone.project,
		"description": milestone.description,
		"milestone_date": milestone.milestone_date,
		"status": milestone.status,
		"priority": milestone.priority,
		"color": milestone.color,
		"progress": milestone.progress,
		"total_tasks": milestone.total_tasks,
		"completed_tasks": milestone.completed_tasks,
		"health": _calculate_milestone_health(milestone.as_dict()),
	}


@frappe.whitelist()
def delete_milestone(milestone_name: str):
	"""
	Delete a milestone.
	All tasks linked to this milestone will have their milestone field cleared.
	"""
	if not milestone_name:
		frappe.throw(_("Milestone name is required"))

	if not frappe.db.exists("Project Milestone", milestone_name):
		frappe.throw(_("Milestone {0} does not exist").format(milestone_name))

	# Unlink all tasks (handled by on_trash hook in doctype)
	frappe.delete_doc("Project Milestone", milestone_name)

	return {"success": True, "message": _("Milestone deleted successfully")}


@frappe.whitelist()
def assign_task_to_milestone(task_name: str, milestone: str | None = None):
	"""
	Assign a task to a milestone or remove milestone assignment.
	Also assigns all subtasks to the same milestone.

	Args:
		task_name: Name of the task to update
		milestone: Name of the milestone to assign, or None/empty to remove assignment

	Validates that task and milestone belong to the same project.
	"""
	if not task_name:
		frappe.throw(_("Task name is required"))

	task = frappe.get_doc("Task", task_name)

	# If assigning to a milestone, validate same project
	if milestone:
		if not frappe.db.exists("Project Milestone", milestone):
			frappe.throw(_("Milestone {0} does not exist").format(milestone))

		milestone_project = frappe.db.get_value("Project Milestone", milestone, "project")

		if task.project != milestone_project:
			frappe.throw(
				_(
					"Task and milestone must belong to the same project. Task is in '{0}', milestone is in '{1}'"
				).format(task.project, milestone_project)
			)

	# Update task
	task.milestone = milestone if milestone else None
	task.save()

	# Also update all subtasks recursively
	subtasks_updated = _update_subtasks_milestone(task_name, milestone)

	# Progress updates are handled by doc_events hooks

	return {
		"success": True,
		"task": task_name,
		"milestone": task.milestone,
		"subtasks_updated": subtasks_updated,
		"message": _("Task and {0} subtasks milestone updated successfully").format(subtasks_updated),
	}


def _update_subtasks_milestone(parent_task: str, milestone: str) -> int:
	"""
	Recursively update milestone for all subtasks.
	Returns count of updated subtasks.
	"""
	subtasks = frappe.get_all("Task", filters={"parent_task": parent_task}, pluck="name")

	count = 0
	for subtask_name in subtasks:
		frappe.db.set_value("Task", subtask_name, "milestone", milestone, update_modified=True)
		count += 1
		# Recursively update children
		count += _update_subtasks_milestone(subtask_name, milestone)

	return count


@frappe.whitelist()
def get_milestone_tasks(milestone_name: str):
	"""
	Get all tasks assigned to a specific milestone.
	"""
	if not milestone_name:
		frappe.throw(_("Milestone name is required"))

	if not frappe.db.exists("Project Milestone", milestone_name):
		frappe.throw(_("Milestone {0} does not exist").format(milestone_name))

	tasks = frappe.get_all(
		"Task",
		filters={"milestone": milestone_name},
		fields=[
			"name",
			"subject",
			"status",
			"priority",
			"exp_end_date",
			"progress",
			"_assign",
		],
		order_by="exp_end_date asc, creation asc",
	)

	return tasks


@frappe.whitelist()
def get_milestone_statuses():
	"""Get available milestone statuses."""
	return ["Open", "In Progress", "Completed", "Cancelled"]


# =============================================================================
# MY TASKS API - Tasks assigned to current user across all projects
# =============================================================================


@frappe.whitelist()
def get_my_tasks(
	status: str | None = None,
	priority: str | None = None,
	project: str | None = None,
	due_filter: str | None = None,
	search: str | None = None,
	sort_by: str = "default",
	sort_order: str = "asc",
	limit: int = 100,
	offset: int = 0,
):
	"""
	Get all tasks assigned to the current user across all projects.

	Args:
		status: Filter by status (comma-separated for multiple)
		priority: Filter by priority (comma-separated for multiple)
		project: Filter by project name
		due_filter: 'today', 'week', 'overdue', 'all'
		search: Search in subject
		sort_by: 'default', 'due_date', 'priority', 'modified', 'subject', 'project', 'status'
		sort_order: 'asc' or 'desc'
		limit: Number of results to return
		offset: Offset for pagination

	Returns:
		List of tasks with project info
	"""
	user = frappe.session.user

	# Build filters
	filters = []
	values = {"user": f'%"{user}"%'}

	# Base filter: assigned to current user
	filters.append("t._assign LIKE %(user)s")

	# Status filter
	if status:
		status_list = [s.strip() for s in status.split(",") if s.strip()]
		if status_list:
			status_placeholders = ", ".join([f"%(status_{i})s" for i in range(len(status_list))])
			filters.append(f"t.status IN ({status_placeholders})")
			for i, s in enumerate(status_list):
				values[f"status_{i}"] = s

	# Priority filter
	if priority:
		priority_list = [p.strip() for p in priority.split(",") if p.strip()]
		if priority_list:
			priority_placeholders = ", ".join([f"%(priority_{i})s" for i in range(len(priority_list))])
			filters.append(f"t.priority IN ({priority_placeholders})")
			for i, p in enumerate(priority_list):
				values[f"priority_{i}"] = p

	# Project filter
	if project:
		filters.append("t.project = %(project)s")
		values["project"] = project

	# Due date filter
	if due_filter:
		from frappe.utils import add_days, today

		today_date = today()

		if due_filter == "today":
			filters.append("t.exp_end_date = %(today)s")
			values["today"] = today_date
		elif due_filter == "week":
			week_end = add_days(today_date, 7)
			filters.append("t.exp_end_date BETWEEN %(today)s AND %(week_end)s")
			values["today"] = today_date
			values["week_end"] = week_end
		elif due_filter == "overdue":
			filters.append(
				"t.exp_end_date IS NOT NULL AND t.exp_end_date != '' AND t.exp_end_date < %(today)s "
				"AND t.status NOT IN ('Completed', 'Cancelled')"
			)
			values["today"] = today_date

	# Search filter
	if search:
		filters.append("t.subject LIKE %(search)s")
		values["search"] = f"%{search}%"

	# Build WHERE clause
	where_clause = " AND ".join(filters) if filters else "1=1"

	# Build ORDER BY clause
	# Note: MariaDB doesn't support NULLS LAST, use ISNULL() or COALESCE instead
	sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

	if sort_by == "due_date":
		order_by = f"ISNULL(t.exp_end_date), t.exp_end_date {sort_direction}, t.modified DESC"
	elif sort_by == "priority":
		priority_order = "ASC" if sort_order.lower() == "asc" else "DESC"
		order_by = f"""
			CASE t.priority
				WHEN 'Urgent' THEN 1
				WHEN 'High' THEN 2
				WHEN 'Medium' THEN 3
				WHEN 'Low' THEN 4
				ELSE 5
			END {priority_order}, ISNULL(t.exp_end_date), t.exp_end_date ASC
		"""
	elif sort_by == "modified":
		order_by = f"t.modified {sort_direction}"
	elif sort_by == "subject":
		order_by = f"t.subject {sort_direction}, t.modified DESC"
	elif sort_by == "project":
		order_by = f"ISNULL(p.project_name), p.project_name {sort_direction}, t.modified DESC"
	elif sort_by == "status":
		order_by = f"t.status {sort_direction}, t.modified DESC"
	else:
		# Default: overdue first, then by due date, then by modified
		from frappe.utils import today

		values["sort_today"] = today()
		order_by = """
			CASE
				WHEN t.exp_end_date < %(sort_today)s AND t.status NOT IN ('Completed', 'Cancelled') THEN 0
				ELSE 1
			END ASC,
			ISNULL(t.exp_end_date), t.exp_end_date ASC,
			t.modified DESC
		"""

	# Execute query
	query = (
		"""
		SELECT
			t.name,
			t.subject,
			t.parent_task,
			parent.subject as parent_subject,
			t.status,
			t.priority,
			t.project,
			t.exp_start_date,
			t.exp_end_date,
			t.description,
			t.progress,
			t.expected_time,
			t._assign,
			t.modified,
			t.creation,
			p.project_name
		FROM `tabTask` t
		LEFT JOIN `tabTask` parent ON t.parent_task = parent.name
		LEFT JOIN `tabProject` p ON t.project = p.name
		WHERE """
		+ where_clause
		+ """
		ORDER BY """
		+ order_by
		+ """
		LIMIT %(limit)s OFFSET %(offset)s
	"""
	)
	tasks = frappe.db.sql(query, {**values, "limit": int(limit), "offset": int(offset)}, as_dict=True)

	# Get total count for pagination
	count_query = (
		"""
		SELECT COUNT(*) as count
		FROM `tabTask` t
		WHERE """
		+ where_clause
		+ """
	"""
	)
	total_count = frappe.db.sql(count_query, values, as_dict=True)[0].get("count", 0)

	# Add overdue flag
	from frappe.utils import getdate, today

	today_date = getdate(today())
	for task in tasks:
		if task.get("exp_end_date"):
			task["is_overdue"] = getdate(task["exp_end_date"]) < today_date and task["status"] not in [
				"Completed",
				"Cancelled",
			]
		else:
			task["is_overdue"] = False

	return {
		"tasks": tasks,
		"total": total_count,
		"limit": limit,
		"offset": offset,
	}


@frappe.whitelist()
def get_my_tasks_projects():
	"""
	Get list of projects where current user has assigned tasks.
	Used for project filter dropdown.
	"""
	user = frappe.session.user

	projects = frappe.db.sql(
		"""
		SELECT DISTINCT
			p.name,
			p.project_name,
			p.status,
			COUNT(t.name) as task_count
		FROM `tabTask` t
		INNER JOIN `tabProject` p ON t.project = p.name
		WHERE t._assign LIKE %s
		AND p.status != 'Cancelled'
		GROUP BY p.name, p.project_name, p.status
		ORDER BY p.project_name
	""",
		(f'%"{user}"%',),
		as_dict=True,
	)

	return projects


@frappe.whitelist()
def quick_update_task(
	task_name: str,
	status: str | None = None,
	priority: str | None = None,
	exp_end_date: str | None = None,
):
	"""
	Quick update for task status, priority, or due date.
	Used for inline editing in My Tasks view.
	Returns updated task data.
	"""
	if not task_name:
		frappe.throw(_("Task name is required"))

	task = frappe.get_doc("Task", task_name)

	# Check if trying to set status to Completed
	if status == "Completed":
		incomplete_subtasks = _get_incomplete_subtasks(task_name)
		if incomplete_subtasks:
			subtask_names = ", ".join([s["subject"] for s in incomplete_subtasks[:3]])
			if len(incomplete_subtasks) > 3:
				subtask_names += f" and {len(incomplete_subtasks) - 3} more"

			frappe.msgprint(
				_("Cannot complete task. {0} subtask(s) are not completed: {1}").format(
					len(incomplete_subtasks), subtask_names
				),
				title=_("Complete Subtasks First"),
				indicator="blue",
			)
			# Return current task state without changes
			return _get_task_response(task)

	# Update fields
	if status is not None:
		task.status = status
		if status == "Completed":
			task.progress = 100

	if priority is not None:
		task.priority = priority

	if exp_end_date is not None:
		task.exp_end_date = exp_end_date if exp_end_date else None

	task.save()

	return _get_task_response(task)


def _get_task_response(task):
	"""Helper to format task response with project info."""
	from frappe.utils import getdate, today

	project_name = None
	if task.project:
		project_name = frappe.db.get_value("Project", task.project, "project_name")

	parent_subject = None
	if getattr(task, "parent_task", None):
		parent_subject = frappe.db.get_value("Task", task.parent_task, "subject")

	is_overdue = False
	if task.exp_end_date:
		is_overdue = getdate(task.exp_end_date) < getdate(today()) and task.status not in [
			"Completed",
			"Cancelled",
		]

	return {
		"name": task.name,
		"subject": task.subject,
		"parent_task": getattr(task, "parent_task", None),
		"parent_subject": parent_subject,
		"status": task.status,
		"priority": task.priority,
		"project": task.project,
		"project_name": project_name,
		"exp_start_date": task.exp_start_date,
		"exp_end_date": task.exp_end_date,
		"description": task.description,
		"progress": task.progress,
		"expected_time": getattr(task, "expected_time", None),
		"_assign": task._assign,
		"modified": task.modified,
		"is_overdue": is_overdue,
	}


@frappe.whitelist()
def shift_overdue_due_dates(limit: int = 100):
	"""
	Shift overdue tasks assigned to the current user by two days.
	"""
	user = frappe.session.user
	if not limit or limit <= 0:
		limit = 100

	from frappe.utils import add_days, getdate, today

	today_date = getdate(today())
	tasks = frappe.get_all(
		"Task",
		filters={
			"_assign": ["like", f'%"{user}"%'],
			"exp_end_date": ["<", today_date],
			"status": ["not in", ["Completed", "Cancelled"]],
		},
		fields=["name", "exp_end_date"],
		limit=int(limit),
	)

	shifted = 0
	for task in tasks:
		due_date = task.get("exp_end_date")
		if not due_date:
			continue

		try:
			new_due = add_days(due_date, 2)
			frappe.db.set_value("Task", task["name"], "exp_end_date", new_due, update_modified=True)
			shifted += 1
		except Exception as exc:
			frappe.log_error(
				f"Failed to shift overdue task due date: {task['name']} ({exc})",
				"Shift Overdue Due Dates",
			)

	return {"shifted": shifted}


@frappe.whitelist()
def get_task_detail(task_name: str):
	"""
	Get full task details for drawer/edit view.
	"""
	if not task_name:
		frappe.throw(_("Task name is required"))

	task = frappe.get_doc("Task", task_name)

	return _get_task_response(task)


@frappe.whitelist()
def get_task_subtasks(task_name: str):
	"""
	Get direct subtasks for a task, sorted by idx.
	Returns all subtasks regardless of UI filters.
	"""
	if not task_name:
		frappe.throw(_("Task name is required"))

	if not frappe.db.exists("Task", task_name):
		frappe.throw(_("Task {0} does not exist").format(task_name))

	return frappe.get_all(
		"Task",
		filters={"parent_task": task_name},
		fields=[
			"name",
			"subject",
			"status",
			"priority",
			"parent_task",
			"project",
			"exp_end_date",
			"progress",
			"idx",
		],
		order_by="idx asc, creation asc",
	)


@frappe.whitelist()
def create_my_task(
	subject: str,
	project: str,
	parent_task: str | None = None,
	priority: str = "Medium",
	status: str = "Open",
	exp_end_date: str | None = None,
	description: str | None = None,
	expected_time: float | None = None,
):
	"""
	Create a new task and assign it to the current user.
	"""
	if not subject or not project:
		frappe.throw(_("Subject and Project are required"))

	user = frappe.session.user

	# If parent_task is provided, ensure it's a group task
	if parent_task:
		parent = frappe.get_doc("Task", parent_task)
		if not parent.is_group:
			parent.is_group = 1
			parent.save()

	# Create task
	task = frappe.get_doc(
		{
			"doctype": "Task",
			"subject": subject,
			"project": project,
			"parent_task": parent_task,
			"priority": priority,
			"status": status,
			"exp_end_date": exp_end_date,
			"description": description,
			"expected_time": expected_time,
		}
	)
	task.insert()

	# Assign to current user
	from frappe.desk.form.assign_to import add as add_assignment

	add_assignment(
		{
			"doctype": "Task",
			"name": task.name,
			"assign_to": [user],
		}
	)

	# Reload to get _assign field
	task.reload()

	return _get_task_response(task)


@frappe.whitelist()
def get_projects_settings():
	"""
	Get Projects Settings including global default activity type.
	Returns a dict with all settings values.
	"""
	try:
		# Get the single Projects Settings document
		settings = frappe.get_single("Projects Settings")

		return {
			"default_activity_type": settings.get("default_activity_type"),
			# Add other settings fields as needed
			"ignore_workstation_time_overlap": settings.get("ignore_workstation_time_overlap", False),
			"ignore_user_time_overlap": settings.get("ignore_user_time_overlap", False),
			"ignore_employee_time_overlap": settings.get("ignore_employee_time_overlap", False),
			"fetch_timesheet_in_sales_invoice": settings.get("fetch_timesheet_in_sales_invoice", False),
		}
	except frappe.DoesNotExistError as e:
		frappe.log_error(f"Error fetching Projects Settings: {e!s}", "Projects Settings Error")
		# Return default values if settings not found
		return {
			"default_activity_type": None,
			"ignore_workstation_time_overlap": False,
			"ignore_user_time_overlap": False,
			"ignore_employee_time_overlap": False,
			"fetch_timesheet_in_sales_invoice": False,
		}


@frappe.whitelist()
def get_task_attachments(task_name: str):
	"""Get all file attachments for a task."""
	return _get_document_attachments("Task", task_name)


@frappe.whitelist()
def get_project_attachments(project_name: str):
	"""Get all file attachments for a project."""
	return _get_document_attachments("Project", project_name)


@frappe.whitelist()
def get_task_comments(task_name: str):
	"""Get standard Comment records for a task."""
	if not task_name:
		frappe.throw(_("Task name is required"))

	frappe.has_permission("Task", "read", task_name, throw=True)

	return frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Task",
			"reference_name": task_name,
			"comment_type": "Comment",
		},
		fields=["name", "content", "creation", "owner", "comment_by", "comment_email", "published"],
		order_by="creation desc",
	)


@frappe.whitelist(methods=["POST"])
def add_task_comment(task_name: str, content: str):
	"""Create a standard Comment on a task."""
	if not task_name:
		frappe.throw(_("Task name is required"))
	if not content or not content.strip():
		frappe.throw(_("The comment cannot be empty"))

	task = frappe.get_doc("Task", task_name)
	task.check_permission("read")

	comment = task.add_comment(
		text=content.strip(),
		comment_email=frappe.session.user,
		comment_by=frappe.session.user,
	)
	return {
		"name": comment.name,
		"content": comment.content,
		"creation": comment.creation,
		"owner": comment.owner,
		"comment_by": comment.comment_by,
		"comment_email": comment.comment_email,
		"published": comment.published,
	}


@frappe.whitelist()
def delete_task_attachment(file_name: str):
	"""Delete a file attachment from a task."""
	return _delete_document_attachment("Task", file_name)


@frappe.whitelist()
def delete_project_attachment(file_name: str):
	"""Delete a file attachment from a project."""
	return _delete_document_attachment("Project", file_name)
