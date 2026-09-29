"""Work planning tab of Projekt HUB.

Planners (users who can create Work Plan Entry) plan how many hours each employee
works on which project on each day of a week, against the employee's availability
(see erpnext_projekt_hub.availability). Everyone else sees their own plan only.
"""

import json
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate

from erpnext_projekt_hub.access import has_project_hub_access
from erpnext_projekt_hub.availability import DEFAULT_DAILY_HOURS, get_availability

ENTRY_FIELDS = ["name", "employee", "date", "project", "project_name", "hours", "note"]


def _check_access():
	if not has_project_hub_access():
		frappe.throw(_("You do not have permission to access Projekt HUB"), frappe.PermissionError)


def _can_plan() -> bool:
	return bool(frappe.has_permission("Work Plan Entry", "create"))


def _check_can_plan():
	_check_access()
	if not _can_plan():
		frappe.throw(_("You do not have permission to plan work"), frappe.PermissionError)


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
	can_plan = _can_plan()

	if can_plan:
		employees = _get_employees(department=department)
	else:
		own_employee = frappe.db.get_value(
			"Employee", {"user_id": frappe.session.user, "status": "Active"}, "name"
		)
		employees = _get_employees(employee=own_employee) if own_employee else []

	employee_names = [row.name for row in employees]
	plan = defaultdict(lambda: defaultdict(list))
	for entry in _get_entries(employee_names, dates):
		entry.date = str(entry.date)
		entry.hours = flt(entry.hours, 2)
		plan[entry.employee][entry.date].append(entry)

	departments = []
	if can_plan:
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
		"can_plan": can_plan,
		"departments": departments,
		"default_daily_hours": DEFAULT_DAILY_HOURS,
	}


@frappe.whitelist()
def get_plannable_projects(employee: str | None = None) -> list[dict]:
	"""Return open projects, the ones the employee is a member of first."""
	_check_can_plan()

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
	_check_can_plan()

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
	_check_can_plan()

	entry = frappe.get_doc("Work Plan Entry", name)
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
	_check_can_plan()
	frappe.delete_doc("Work Plan Entry", name)


@frappe.whitelist(methods=["POST"])
def copy_previous_week(week_start: str, department: str | None = None) -> dict:
	"""Copy last week's plan into this week, day by day.

	Days on which the employee is not available this week, and days already planned
	on the same project, are skipped.
	"""
	_check_can_plan()

	dates = _get_week_dates(week_start)
	previous_dates = [add_days(day, -7) for day in dates]
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
