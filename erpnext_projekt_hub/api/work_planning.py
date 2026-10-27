"""Work planning tab of Projekt HUB.

Planners (see access.PLANNER_ROLES) plan how many hours each employee works on which
project on each day of a week, against the employee's availability (see
erpnext_projekt_hub.availability). Everybody else plans the days of their own Employee
record only, so nobody changes a colleague's plan; the Work Plan Entry controller
enforces the same rule on every write, and track_changes keeps the history.
"""

import json
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate

from erpnext_projekt_hub.access import can_plan_for_others, get_own_employee, has_project_hub_access
from erpnext_projekt_hub.availability import DEFAULT_DAILY_HOURS, get_availability

ENTRY_FIELDS = ["name", "employee", "date", "project", "project_name", "hours", "note"]
FORECAST_TASK_STATUSES = ["Open", "Working", "Pending Review"]


def _check_access():
	if not has_project_hub_access():
		frappe.throw(_("You do not have permission to access Projekt HUB"), frappe.PermissionError)


def _can_write_entries() -> bool:
	"""Whether the DocType's role permissions let the user create plan entries at all."""
	return bool(frappe.has_permission("Work Plan Entry", "create"))


def _check_can_plan(employee: str | None = None) -> str | None:
	"""Throw unless the user may plan `employee`, and return the employee they are limited to.

	None means no limit: a planner plans the whole team. Anybody else is limited to
	their own Employee record, so passing a different `employee` is refused.
	"""
	_check_access()
	if not _can_write_entries():
		frappe.throw(_("You do not have permission to plan work"), frappe.PermissionError)

	if can_plan_for_others():
		return None

	own_employee = get_own_employee()
	if not own_employee:
		frappe.throw(_("Your user is not linked to an active employee"), frappe.PermissionError)
	if employee and employee != own_employee:
		frappe.throw(_("You can only plan your own work"), frappe.PermissionError)

	return own_employee


def _get_week_dates(week_start) -> list:
	"""Return Monday to Sunday of the week that contains week_start."""
	day = getdate(week_start)
	monday = add_days(day, -day.weekday())
	return [add_days(monday, offset) for offset in range(7)]


def _get_employees(department: str | None = None, employee: str | None = None) -> list[dict]:
	filters = {"status": "Active"}
	if employee:
		filters["name"] = employee
	elif department:
		filters["department"] = department

	return frappe.get_all(
		"Employee",
		filters=filters,
		fields=["name", "employee_name", "designation", "department", "image"],
		order_by="employee_name asc",
	)


def _get_entries(employees: list[str], dates: list) -> list[dict]:
	if not employees:
		return []

	return frappe.get_all(
		"Work Plan Entry",
		filters={"employee": ("in", employees), "date": ("between", [dates[0], dates[-1]])},
		fields=ENTRY_FIELDS,
		order_by="date asc, creation asc",
	)


def _get_overbooked_days(employee: str, dates: list) -> list[dict]:
	"""Days on which the employee is planned for more hours than they are available."""
	availability = get_availability([employee], dates).get(employee, {})
	planned = defaultdict(float)
	for entry in _get_entries([employee], sorted(dates)):
		planned[str(entry.date)] += flt(entry.hours)

	return [
		{"date": day, "planned": flt(hours, 2), "available": availability.get(day, {}).get("hours", 0)}
		for day, hours in sorted(planned.items())
		if hours - availability.get(day, {}).get("hours", 0) > 0.001
	]


@frappe.whitelist()
def get_work_plan(week_start: str, department: str | None = None) -> dict:
	"""Return the plan and availability of employees for the week containing week_start."""
	_check_access()

	dates = _get_week_dates(week_start)
	own_employee = get_own_employee()
	can_write = _can_write_entries()
	plan_for_others = can_write and can_plan_for_others()

	if plan_for_others:
		employees = _get_employees(department=department)
	else:
		employees = _get_employees(employee=own_employee) if own_employee else []

	employee_names = [row.name for row in employees]
	plan = defaultdict(lambda: defaultdict(list))
	for entry in _get_entries(employee_names, dates):
		entry.date = str(entry.date)
		entry.hours = flt(entry.hours, 2)
		plan[entry.employee][entry.date].append(entry)

	departments = []
	if plan_for_others:
		departments = sorted(
			set(
				frappe.get_all(
					"Employee",
					filters={"status": "Active", "department": ("is", "set")},
					pluck="department",
				)
			)
		)

	return {
		"week_start": str(dates[0]),
		"dates": [str(day) for day in dates],
		"employees": employees,
		"availability": get_availability(employee_names, dates),
		"plan": plan,
		# can_plan says the user may plan something, own_employee which row that is
		# when they are not a planner: the UI opens the editor for that row only.
		"can_plan": plan_for_others or (can_write and bool(own_employee)),
		"can_plan_for_others": plan_for_others,
		"own_employee": own_employee,
		"departments": departments,
		"default_daily_hours": DEFAULT_DAILY_HOURS,
	}


def _working_days(start, end) -> list:
	"""Return weekdays in an inclusive date range."""
	start = getdate(start)
	end = getdate(end)
	days = []
	current = start
	while current <= end:
		if current.weekday() < 5:
			days.append(current)
		current = add_days(current, 1)
	return days


def _remaining_task_hours(task) -> float:
	"""Return remaining effort, using actual time when it is available."""
	expected = max(flt(task.expected_time), 0)
	if not expected:
		return 0.0

	actual = max(flt(task.actual_time), 0)
	if actual:
		return max(expected - actual, 0.0)

	progress = min(max(flt(task.progress), 0), 100)
	return max(expected * (1 - progress / 100), 0.0)


def _task_period_demand(task, period_start, period_end, remaining_hours: float) -> float:
	"""Allocate task effort proportionally to working days in the selected period."""
	if not remaining_hours:
		return 0.0

	period_start = getdate(period_start)
	period_end = getdate(period_end)
	task_start = getdate(task.exp_start_date) if task.exp_start_date else None
	task_end = getdate(task.exp_end_date) if task.exp_end_date else None
	if not task_start and not task_end:
		return 0.0

	task_start = task_start or period_start
	task_end = task_end or period_end
	if task_start > task_end or task_end < period_start or task_start > period_end:
		return 0.0

	total_days = len(_working_days(task_start, task_end))
	overlap_start = max(task_start, period_start)
	overlap_end = min(task_end, period_end)
	overlap_days = len(_working_days(overlap_start, overlap_end))
	if not total_days or not overlap_days:
		return 0.0

	return flt(remaining_hours * overlap_days / total_days, 2)


@frappe.whitelist()
def get_work_forecast(start_date: str, end_date: str, department: str | None = None) -> dict:
	"""Return capacity, planned hours and task demand for a selected period."""
	_check_access()

	period_start = getdate(start_date)
	period_end = getdate(end_date)
	if period_start > period_end:
		frappe.throw(_("Start date cannot be after end date"))

	own_employee = get_own_employee()
	can_write = _can_write_entries()
	plan_for_others = can_write and can_plan_for_others()
	if plan_for_others:
		employees = _get_employees(department=department)
	else:
		employees = _get_employees(employee=own_employee) if own_employee else []

	employee_names = [employee.name for employee in employees]
	dates = []
	current = period_start
	while current <= period_end:
		dates.append(current)
		current = add_days(current, 1)

	availability = get_availability(employee_names, dates)
	entries = _get_entries(employee_names, dates)

	planned_by_employee = defaultdict(float)
	planned_by_project = defaultdict(float)
	for entry in entries:
		planned_by_employee[entry.employee] += flt(entry.hours)
		planned_by_project[entry.project] += flt(entry.hours)

	users = (
		frappe.get_all("Employee", filters={"name": ("in", employee_names)}, fields=["name", "user_id"])
		if employee_names
		else []
	)
	user_to_employee = {row.user_id: row.name for row in users if row.user_id}
	assigned_users = list(user_to_employee)
	todo_rows = (
		frappe.get_all(
			"ToDo",
			filters={
				"allocated_to": ("in", assigned_users),
				"reference_type": "Task",
				"status": "Open",
			},
			fields=["allocated_to", "reference_name"],
		)
		if assigned_users
		else []
	)
	task_employees = defaultdict(set)
	for row in todo_rows:
		task_employees[row.reference_name].add(user_to_employee[row.allocated_to])

	task_ids = list(task_employees)
	tasks = (
		frappe.get_all(
			"Task",
			filters={"name": ("in", task_ids), "status": ("in", FORECAST_TASK_STATUSES)},
			fields=[
				"name",
				"subject",
				"project",
				"status",
				"expected_time",
				"actual_time",
				"progress",
				"exp_start_date",
				"exp_end_date",
			],
			order_by="exp_end_date, subject",
		)
		if task_ids
		else []
	)

	project_ids = {task.project for task in tasks if task.project}
	project_ids.update(entry.project for entry in entries if entry.project)
	project_names = {}
	if project_ids:
		project_names = {
			row.name: row.project_name
			for row in frappe.get_all(
				"Project", filters={"name": ("in", list(project_ids))}, fields=["name", "project_name"]
			)
		}

	people = {}
	for employee in employees:
		available = round(sum(day.get("hours", 0) for day in availability.get(employee.name, {}).values()), 2)
		people[employee.name] = {
			"employee": employee.name,
			"employee_name": employee.employee_name,
			"designation": employee.designation,
			"department": employee.department,
			"image": employee.image,
			"available_hours": available,
			"planned_hours": round(planned_by_employee[employee.name], 2),
			"demand_hours": 0.0,
			"uncovered_hours": 0.0,
			"tasks": [],
		}

	project_summary = {}
	for project in project_ids:
		project_summary[project] = {
			"project": project,
			"project_name": project_names.get(project, project),
			"planned_hours": round(planned_by_project[project], 2),
			"demand_hours": 0.0,
			"employees": set(),
		}

	undated_backlog = 0.0
	for task in tasks:
		assigned_employee_names = sorted(task_employees.get(task.name, set()))
		if not assigned_employee_names:
			continue

		remaining_hours = _remaining_task_hours(task)
		if not remaining_hours:
			continue
		period_demand = _task_period_demand(task, period_start, period_end, remaining_hours)
		is_undated = not task.exp_start_date and not task.exp_end_date
		if not period_demand and not is_undated:
			continue
		share = period_demand / len(assigned_employee_names) if assigned_employee_names else 0
		remaining_share = remaining_hours / len(assigned_employee_names)
		if is_undated:
			undated_backlog += remaining_hours

		for employee_name in assigned_employee_names:
			person = people.get(employee_name)
			if not person:
				continue
			person["demand_hours"] += share
			person["tasks"].append(
				{
					"name": task.name,
					"subject": task.subject,
					"project": task.project,
					"project_name": project_names.get(task.project, task.project or _("No project")),
					"status": task.status,
					"progress": flt(task.progress),
					"remaining_hours": flt(remaining_share, 2),
					"demand_hours": flt(share, 2),
					"due_date": str(task.exp_end_date) if task.exp_end_date else None,
					"is_undated": is_undated,
				}
			)
			if task.project in project_summary:
				project_summary[task.project]["demand_hours"] += share
				project_summary[task.project]["employees"].update(assigned_employee_names)

	for person in people.values():
		person["demand_hours"] = round(person["demand_hours"], 2)
		person["uncovered_hours"] = round(max(person["demand_hours"] - person["planned_hours"], 0), 2)
		person["free_hours"] = round(max(person["available_hours"] - person["planned_hours"], 0), 2)
		person["utilization"] = (
			round(person["planned_hours"] / person["available_hours"] * 100, 1)
			if person["available_hours"]
			else 0
		)
		person["forecast_utilization"] = (
			round(person["demand_hours"] / person["available_hours"] * 100, 1)
			if person["available_hours"]
			else 0
		)
		person["tasks"].sort(key=lambda task: (task["due_date"] or "9999-12-31", task["subject"] or ""))

	projects = []
	for project in project_summary.values():
		project["planned_hours"] = round(project["planned_hours"], 2)
		project["demand_hours"] = round(project["demand_hours"], 2)
		if not project["planned_hours"] and not project["demand_hours"]:
			continue
		project["uncovered_hours"] = round(max(project["demand_hours"] - project["planned_hours"], 0), 2)
		project["employees"] = len(project["employees"])
		projects.append(project)
	projects.sort(key=lambda project: project["demand_hours"], reverse=True)

	available_hours = round(sum(person["available_hours"] for person in people.values()), 2)
	planned_hours = round(sum(person["planned_hours"] for person in people.values()), 2)
	demand_hours = round(sum(person["demand_hours"] for person in people.values()), 2)

	return {
		"start_date": str(period_start),
		"end_date": str(period_end),
		"employees": list(people.values()),
		"projects": projects,
		"summary": {
			"available_hours": available_hours,
			"planned_hours": planned_hours,
			"demand_hours": demand_hours,
			"uncovered_hours": round(max(demand_hours - planned_hours, 0), 2),
			"free_hours": round(max(available_hours - planned_hours, 0), 2),
			"utilization": round(planned_hours / available_hours * 100, 1) if available_hours else 0,
			"forecast_utilization": round(demand_hours / available_hours * 100, 1) if available_hours else 0,
			"undated_backlog_hours": round(undated_backlog, 2),
		},
	}


@frappe.whitelist()
def get_plannable_projects(employee: str | None = None) -> list[dict]:
	"""Return open projects, the ones the employee is a member of first."""
	employee = _check_can_plan(employee) or employee

	projects = frappe.get_all(
		"Project",
		filters={"status": "Open", "is_active": ("!=", "No")},
		fields=["name", "project_name", "customer"],
	)

	member_projects = set()
	if employee:
		user_id = frappe.db.get_value("Employee", employee, "user_id")
		if user_id:
			member_projects.update(
				frappe.get_all(
					"Project User", filters={"parenttype": "Project", "user": user_id}, pluck="parent"
				)
			)
		# Project team from the project_control app, when installed.
		if frappe.db.exists("DocType", "Project Employee"):
			member_projects.update(
				frappe.get_all(
					"Project Employee",
					filters={"parenttype": "Project", "employee": employee},
					pluck="parent",
				)
			)

	for project in projects:
		project["is_member"] = project.name in member_projects

	projects.sort(key=lambda project: (not project.is_member, (project.project_name or project.name).lower()))
	return projects


@frappe.whitelist(methods=["POST"])
def save_plan_entries(employee: str, project: str, allocations: str | list, note: str | None = None) -> dict:
	"""Plan the employee on the project: allocations is a list of {"date", "hours"}.

	A day the employee is already planned on this project gets its hours replaced.
	"""
	_check_can_plan(employee)

	if isinstance(allocations, str):
		allocations = json.loads(allocations)
	if not allocations:
		frappe.throw(_("Select at least one day"))

	dates = []
	for allocation in allocations:
		day = getdate(allocation.get("date"))
		hours = flt(allocation.get("hours"), 2)
		existing = frappe.db.get_value(
			"Work Plan Entry", {"employee": employee, "date": day, "project": project}, "name"
		)
		if existing:
			entry = frappe.get_doc("Work Plan Entry", existing)
			entry.hours = hours
			if note is not None:
				entry.note = note
			entry.save()
		else:
			frappe.get_doc(
				{
					"doctype": "Work Plan Entry",
					"employee": employee,
					"date": day,
					"project": project,
					"hours": hours,
					"note": note,
				}
			).insert()
		dates.append(day)

	return {"saved": len(dates), "overbooked": _get_overbooked_days(employee, dates)}


@frappe.whitelist(methods=["POST"])
def update_plan_entry(
	name: str, hours: float | None = None, project: str | None = None, note: str | None = None
) -> dict:
	"""Change the hours, project or note of one plan entry."""
	entry = frappe.get_doc("Work Plan Entry", name)
	_check_can_plan(entry.employee)

	if hours is not None:
		entry.hours = flt(hours, 2)
	if project:
		entry.project = project
	if note is not None:
		entry.note = note
	entry.save()

	return {"name": entry.name, "overbooked": _get_overbooked_days(entry.employee, [getdate(entry.date)])}


@frappe.whitelist(methods=["POST"])
def delete_plan_entry(name: str) -> None:
	_check_can_plan(frappe.db.get_value("Work Plan Entry", name, "employee"))
	frappe.delete_doc("Work Plan Entry", name)


@frappe.whitelist(methods=["POST"])
def copy_previous_week(week_start: str, department: str | None = None) -> dict:
	"""Copy last week's plan into this week, day by day.

	Days on which the employee is not available this week, and days already planned
	on the same project, are skipped. Without the right to plan others, only the
	caller's own week is copied.
	"""
	own_employee = _check_can_plan()

	dates = _get_week_dates(week_start)
	previous_dates = [add_days(day, -7) for day in dates]
	if own_employee:
		employees = [own_employee]
	else:
		employees = [row.name for row in _get_employees(department=department)]

	availability = get_availability(employees, dates)
	already_planned = {
		(entry.employee, str(entry.date), entry.project) for entry in _get_entries(employees, dates)
	}

	copied = skipped_unavailable = skipped_planned = 0
	for entry in _get_entries(employees, previous_dates):
		day = str(add_days(entry.date, 7))
		if availability.get(entry.employee, {}).get(day, {}).get("hours", 0) <= 0:
			skipped_unavailable += 1
			continue
		if (entry.employee, day, entry.project) in already_planned:
			skipped_planned += 1
			continue

		frappe.get_doc(
			{
				"doctype": "Work Plan Entry",
				"employee": entry.employee,
				"date": day,
				"project": entry.project,
				"hours": entry.hours,
				"note": entry.note,
			}
		).insert()
		copied += 1

	return {"copied": copied, "skipped_unavailable": skipped_unavailable, "skipped_planned": skipped_planned}
