"""
Project Outliner API endpoints for task management.
Provides CRUD operations for tasks in a hierarchical tree view.
"""

import frappe
from frappe import _


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
def get_project_tasks(project: str):
	"""
	Get all tasks for a project with hierarchical structure.
	Returns tasks sorted by parent and idx for tree building.
	"""
	if not project:
		frappe.throw(_("Project is required"))

	# Get project details
	project_doc = frappe.get_doc("Project", project)

	# Get all tasks for this project
	tasks = frappe.get_all(
		"Task",
		filters={"project": project},
		fields=[
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
		],
		order_by="parent_task, idx, creation",
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

	return {
		"project": {
			"name": project_doc.name,
			"project_name": project_doc.project_name,
			"status": project_doc.status,
			"percent_complete": project_doc.percent_complete,
			"expected_start_date": project_doc.expected_start_date,
			"expected_end_date": project_doc.expected_end_date,
			"actual_start_date": getattr(project_doc, "actual_start_date", None),
			"actual_end_date": getattr(project_doc, "actual_end_date", None),
			"customer": project_doc.customer,
			"customer_name": customer_name,
			"notes": getattr(project_doc, "notes", None),
			"total_hours": total_hours[0].get("total_hours", 0) if total_hours else 0,
			"estimated_hours": estimated_hours[0].get("estimated_hours", 0) if estimated_hours else 0,
		},
		"tasks": tasks,
	}


@frappe.whitelist()
def update_project(
	project: str,
	expected_start_date: str | None = None,
	expected_end_date: str | None = None,
):
	if not project:
		frappe.throw(_("Project is required"))

	project_doc = frappe.get_doc("Project", project)

	if not frappe.has_permission("Project", "write", doc=project_doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if expected_start_date == "":
		expected_start_date = None
	if expected_end_date == "":
		expected_end_date = None

	# Update fields directly in database to avoid triggering notifications
	if expected_start_date is not None:
		frappe.db.set_value("Project", project, "expected_start_date", expected_start_date)
	if expected_end_date is not None:
		frappe.db.set_value("Project", project, "expected_end_date", expected_end_date)

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
		"percent_complete": project_doc.percent_complete,
		"expected_start_date": project_doc.expected_start_date,
		"expected_end_date": project_doc.expected_end_date,
		"actual_start_date": getattr(project_doc, "actual_start_date", None),
		"actual_end_date": getattr(project_doc, "actual_end_date", None),
		"customer": project_doc.customer,
		"customer_name": customer_name,
		"notes": getattr(project_doc, "notes", None),
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

	task.save()

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
		"project": task.project,
		"expected_time": getattr(task, "expected_time", None),
	}


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

	frappe.db.commit()

	return {"success": True}


@frappe.whitelist()
def get_users():
	"""Get list of users that can be assigned to tasks."""
	users = frappe.get_all(
		"User",
		filters={
			"enabled": 1,
			"user_type": "System User",
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
					frappe.db.commit()
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
	frappe.db.commit()

	return {"success": True}


@frappe.whitelist()
def remove_project_user(project: str, user: str):
	"""Remove a user from a project."""
	if not project or not user:
		frappe.throw(_("Project and user are required"))

	# Delete directly from child table to avoid email notifications
	frappe.db.delete("Project User", {"parent": project, "user": user})
	frappe.db.commit()

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
def create_timelog(
	task: str,
	hours: float,
	activity_type: str | None = "Execution",
	description: str | None = None,
	from_time: str | None = None,
	to_time: str | None = None,
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

	if existing_timesheet:
		timesheet = frappe.get_doc("Timesheet", existing_timesheet[0].name)
		# Add time log detail to existing timesheet
		timesheet.append(
			"time_logs",
			{
				"activity_type": activity_type,
				"hours": hours,
				"from_time": from_time or frappe.utils.now(),
				"to_time": to_time or frappe.utils.now(),
				"description": description or "",
				"task": task,
				"project": task_doc.project,
			},
		)
		timesheet.save()
	else:
		# Create new timesheet with time log in one go
		timesheet = frappe.get_doc(
			{
				"doctype": "Timesheet",
				"employee": get_employee_for_user(user),
				"start_date": today,
				"end_date": today,
				"time_logs": [
					{
						"activity_type": activity_type,
						"hours": hours,
						"from_time": from_time or frappe.utils.now(),
						"to_time": to_time or frappe.utils.now(),
						"description": description or "",
						"task": task,
						"project": task_doc.project,
					}
				],
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

	timesheet.save()

	return {
		"timelog_name": timelog.name,
		"hours": timelog.hours,
		"activity_type": timelog.activity_type,
		"description": timelog.description,
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
		],
		order_by="milestone_date asc, creation asc",
	)

	for milestone in milestones:
		# Calculate health status
		milestone["health"] = _calculate_milestone_health(milestone)

	return milestones


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
		sort_by: 'default' (overdue first, then by due date), 'due_date', 'priority', 'modified'
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
			filters.append("t.exp_end_date < %(today)s AND t.status NOT IN ('Completed', 'Cancelled')")
			values["today"] = today_date

	# Search filter
	if search:
		filters.append("t.subject LIKE %(search)s")
		values["search"] = f"%{search}%"

	# Build WHERE clause
	where_clause = " AND ".join(filters) if filters else "1=1"

	# Build ORDER BY clause
	# Note: MariaDB doesn't support NULLS LAST, use ISNULL() or COALESCE instead
	if sort_by == "due_date":
		order_by = "ISNULL(t.exp_end_date), t.exp_end_date ASC, t.modified DESC"
	elif sort_by == "priority":
		order_by = """
			CASE t.priority
				WHEN 'Urgent' THEN 1
				WHEN 'High' THEN 2
				WHEN 'Medium' THEN 3
				WHEN 'Low' THEN 4
				ELSE 5
			END ASC, ISNULL(t.exp_end_date), t.exp_end_date ASC
		"""
	elif sort_by == "modified":
		order_by = "t.modified DESC"
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
	tasks = frappe.db.sql(
		f"""
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
		WHERE {where_clause}
		ORDER BY {order_by}
		LIMIT %(limit)s OFFSET %(offset)s
	""",
		{**values, "limit": int(limit), "offset": int(offset)},
		as_dict=True,
	)

	# Get total count for pagination
	total_count = frappe.db.sql(
		f"""
		SELECT COUNT(*) as count
		FROM `tabTask` t
		WHERE {where_clause}
	""",
		values,
		as_dict=True,
	)[0].get("count", 0)

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

	if shifted:
		frappe.db.commit()

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
