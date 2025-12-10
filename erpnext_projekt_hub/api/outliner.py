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
		"Task",
		filters={"parent_task": task_name},
		fields=["name", "subject", "status"]
	)
	
	for subtask in subtasks:
		if subtask["status"] not in ["Completed", "Cancelled"]:
			incomplete.append({"name": subtask["name"], "subject": subtask["subject"]})
		# Check children recursively
		incomplete.extend(_get_incomplete_subtasks(subtask["name"]))
	
	return incomplete


@frappe.whitelist()
def get_projects():
	"""Get list of all projects with task counts."""
	projects = frappe.get_all(
		"Project",
		filters={"status": ["!=", "Cancelled"]},
		fields=[
			"name",
			"project_name",
			"status",
			"percent_complete",
			"expected_start_date",
			"expected_end_date",
			"priority",
		],
		order_by="modified desc",
	)

	# Add task count for each project
	for project in projects:
		project["task_count"] = frappe.db.count("Task", {"project": project["name"]})

	return projects


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
			"description",
			"_assign",
			"idx",
			"creation",
			"modified",
			"project",
		],
		order_by="parent_task, idx, creation",
	)

	return {
		"project": {
			"name": project_doc.name,
			"project_name": project_doc.project_name,
			"status": project_doc.status,
			"percent_complete": project_doc.percent_complete,
			"expected_start_date": project_doc.expected_start_date,
			"expected_end_date": project_doc.expected_end_date,
		},
		"tasks": tasks,
	}


@frappe.whitelist()
def create_task(
	subject: str,
	project: str,
	parent_task: str = None,
	priority: str = "Medium",
	status: str = "Open",
	exp_end_date: str = None,
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
			frappe.throw(
				_("Cannot complete task. {0} subtask(s) are not completed: {1}").format(
					len(incomplete_subtasks), subtask_names
				)
			)

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
	]

	for field in allowed_fields:
		if field in kwargs and kwargs[field] is not None:
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
	}


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
def reorder_task(task_name: str, parent_task: str = None, idx: int = 0):
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
			frappe.throw(
				_("Cannot complete task. {0} subtask(s) are not completed: {1}").format(
					len(incomplete_subtasks), subtask_names
				)
			)
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
def assign_task(task_name: str, user: str = None, action: str = "add"):
	"""Assign or unassign a user to/from a task."""
	if not task_name:
		frappe.throw(_("Task name is required"))

	from frappe.desk.form.assign_to import add as add_assignment, remove as remove_assignment

	if action == "add" and user:
		add_assignment({
			"doctype": "Task",
			"name": task_name,
			"assign_to": [user],
		})
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
		users.append({
			"user": user.user,
			"full_name": user_doc.full_name,
			"user_image": user_doc.user_image,
		})

	return users


@frappe.whitelist()
def add_project_user(project: str, user: str):
	"""Add a user to a project."""
	if not project or not user:
		frappe.throw(_("Project and user are required"))

	# Check if user already exists
	existing = frappe.db.exists("Project User", {
		"parent": project,
		"user": user
	})
	
	if existing:
		return {"message": "User already in project"}

	# Insert directly into child table to avoid email notifications
	project_user = frappe.get_doc({
		"doctype": "Project User",
		"parent": project,
		"parenttype": "Project",
		"parentfield": "users",
		"user": user
	})
	project_user.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"success": True}


@frappe.whitelist()
def remove_project_user(project: str, user: str):
	"""Remove a user from a project."""
	if not project or not user:
		frappe.throw(_("Project and user are required"))

	# Delete directly from child table to avoid email notifications
	frappe.db.delete("Project User", {
		"parent": project,
		"user": user
	})
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
	activity_type: str = "Execution",
	description: str = None,
	from_time: str = None,
	to_time: str = None,
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
		"owner": user,
		"user_full_name": user_doc.full_name,
		"user_image": user_doc.user_image,
	}


@frappe.whitelist()
def update_timelog(
	timelog_name: str,
	hours: float = None,
	activity_type: str = None,
	description: str = None,
	from_time: str = None,
	to_time: str = None,
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

	# Check if user owns this timesheet
	if timesheet.owner != frappe.session.user:
		frappe.throw(_("You can only delete your own time logs"))

	# Remove the time log
	timesheet.time_logs.remove(timelog)
	timesheet.save()

	# If no more time logs, delete the timesheet
	if not timesheet.time_logs:
		frappe.delete_doc("Timesheet", timesheet.name)

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
	description: str = None,
	milestone_date: str = None,
	priority: str = "Medium",
	color: str = None,
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
	new_milestone_name: str = None,
	description: str = None,
	milestone_date: str = None,
	status: str = None,
	priority: str = None,
	color: str = None,
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
def assign_task_to_milestone(task_name: str, milestone: str = None):
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
				_("Task and milestone must belong to the same project. Task is in '{0}', milestone is in '{1}'").format(
					task.project, milestone_project
				)
			)

	# Store old milestone for progress update
	old_milestone = task.milestone

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
	subtasks = frappe.get_all(
		"Task",
		filters={"parent_task": parent_task},
		pluck="name"
	)

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
