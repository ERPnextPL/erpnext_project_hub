"""
Capacity Planning API for Projekt HUB.

Data model: Project Allocation DocType
  - employee       → Link to Employee
  - project        → Link to Project
  - allocation_date → Date  (one record per employee x project x day)
  - hours          → Float (planned hours for that day)
  - notes          → Small Text

Endpoints are restricted to Project Manager / Team Lead / Consultant roles.
"""

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import getdate

DEFAULT_DAILY_HOURS: float = 8.0

_ALLOWED_ROLES = frozenset(
	{"Projects Manager", "Project Manager", "System Manager", "Administrator", "Team Lead", "Consultant"}
)

# Deterministic colour palette — assigned to projects in order of first appearance.
# 12 visually distinct Tailwind-compatible bg/text pairs.
_PROJECT_COLORS = [
	{"bg": "#dbeafe", "text": "#1d4ed8"},  # blue
	{"bg": "#d1fae5", "text": "#065f46"},  # emerald
	{"bg": "#ede9fe", "text": "#6d28d9"},  # violet
	{"bg": "#fef9c3", "text": "#854d0e"},  # yellow
	{"bg": "#fee2e2", "text": "#991b1b"},  # red
	{"bg": "#ffedd5", "text": "#9a3412"},  # orange
	{"bg": "#cffafe", "text": "#155e75"},  # cyan
	{"bg": "#fce7f3", "text": "#9d174d"},  # pink
	{"bg": "#f0fdf4", "text": "#14532d"},  # green
	{"bg": "#faf5ff", "text": "#581c87"},  # purple
	{"bg": "#fff7ed", "text": "#7c2d12"},  # rose-brown
	{"bg": "#ecfdf5", "text": "#064e3b"},  # teal
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_permission() -> None:
	user_roles = set(frappe.get_roles(frappe.session.user))
	if not _ALLOWED_ROLES.intersection(user_roles):
		frappe.throw(_("Permission denied"), frappe.PermissionError)


def _week_days(week_start: str) -> list[str]:
	start = getdate(week_start)
	return [str(start + timedelta(days=i)) for i in range(5)]


def _color_for_project(project: str, color_map: dict) -> dict:
	"""Return a stable bg/text colour dict for the given project name."""
	if project not in color_map:
		idx = len(color_map) % len(_PROJECT_COLORS)
		color_map[project] = _PROJECT_COLORS[idx]
	return color_map[project]


def _has_doctype(doctype: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype))


def _get_week_allocations(
	employees: list[dict], week_start: str, week_end: str, days: list[str]
) -> list[dict]:
	employee_names = [e["name"] for e in employees]
	if not employee_names:
		return []

	project_name_map = {
		p.name: p.project_name
		for p in frappe.get_all(
			"Project",
			fields=["name", "project_name"],
			filters={"status": ["not in", ["Cancelled", "Template"]]},
		)
	}

	if _has_doctype("Project Assignment"):
		assignments = frappe.get_all(
			"Project Assignment",
			filters={
				"employee": ["in", employee_names],
				"from_date": ["<=", week_end],
				"to_date": [">=", week_start],
				"docstatus": ["!=", 2],
				"status": ["!=", "Cancelled"],
			},
			fields=["name", "employee", "project", "from_date", "to_date", "hours_per_day"],
			order_by="from_date, project",
		)

		day_set = set(days)
		allocations: list[dict] = []
		for assignment in assignments:
			start = max(getdate(assignment["from_date"]), getdate(week_start))
			end = min(getdate(assignment["to_date"]), getdate(week_end))
			current = start
			while current <= end:
				current_str = str(current)
				if current_str in day_set:
					allocations.append(
						{
							"name": assignment["name"],
							"employee": assignment["employee"],
							"project": assignment["project"],
							"allocation_date": current_str,
							"hours": assignment.get("hours_per_day") or 0,
							"notes": "",
							"project_name": project_name_map.get(
								assignment["project"], assignment["project"]
							),
						}
					)
				current = current + timedelta(days=1)

		return allocations

	if _has_doctype("Project Allocation"):
		allocations = frappe.get_all(
			"Project Allocation",
			filters={
				"employee": ["in", employee_names],
				"allocation_date": ["between", [week_start, week_end]],
				"docstatus": ["!=", 2],
			},
			fields=["name", "employee", "project", "allocation_date", "hours", "notes"],
			order_by="allocation_date, project",
		)
		for allocation in allocations:
			allocation["project_name"] = project_name_map.get(allocation["project"], allocation["project"])
		return allocations

	frappe.throw(
		_(
			"Capacity Planning is not configured: missing DocType 'Project Assignment' or 'Project Allocation'."
		)
	)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_capacity_planning_data(
	week_start: str,
	project: str | None = None,
	employee_user: str | None = None,
) -> dict:
	"""
	Return weekly capacity planning data built from Project Allocation records.

	Parameters
	----------
	week_start : str
	    ISO date of the Monday (YYYY-MM-DD).
	project : str | None
	    When supplied, only employees with allocations in this project **or**
	    with remaining free capacity are returned.
	    All allocations (across all projects) are still shown per cell so the
	    planner can see the full picture.
	employee_user : str | None
	    Narrow to a single employee (user email). AND logic with `project`.

	Returns
	-------
	dict:
	    week_start, week_end, days, daily_capacity_hours,
	    project_colors, employees
	"""
	_check_permission()

	days = _week_days(week_start)
	week_end = days[-1]
	week_start_str = days[0]

	# ── 1. Active employees ──────────────────────────────────────────────────
	emp_filters: dict = {"status": "Active", "user_id": ["is", "set"]}
	if employee_user:
		emp_filters["user_id"] = employee_user

	employees = frappe.get_all(
		"Employee",
		filters=emp_filters,
		fields=["name", "employee_name", "user_id"],
	)

	if not employees:
		return _empty_response(week_start_str, week_end, days)

	# ── 2. Capacity records for the week ─────────────────────────────────────
	allocations = _get_week_allocations(employees, week_start_str, week_end, days)

	# ── 3. Build per-employee day breakdown ──────────────────────────────────
	# colour map shared across the response so the same project always gets
	# the same colour in the current render
	color_map: dict = {}

	# Pre-collect all project names to assign stable colours in alphabetical order
	all_projects = sorted({a["project"] for a in allocations})
	for proj in all_projects:
		_color_for_project(proj, color_map)

	# Index allocations by (employee_name, date)
	alloc_index: dict[tuple, list] = {}
	for alloc in allocations:
		key = (alloc["employee"], str(alloc["allocation_date"]))
		alloc_index.setdefault(key, []).append(alloc)

	result_employees = []

	for emp in employees:
		emp_name = emp["name"]
		emp_allocs = [a for a in allocations if a["employee"] == emp_name]

		has_project_allocs = bool(project) and any(a["project"] == project for a in emp_allocs)

		days_data: dict[str, dict] = {}

		for day in days:
			day_allocs = alloc_index.get((emp_name, day), [])
			day_planned = sum(float(a["hours"] or 0) for a in day_allocs)
			free_hours = round(max(0.0, DEFAULT_DAILY_HOURS - day_planned), 2)

			days_data[day] = {
				"allocations": [
					{
						"name": a["name"],
						"project": a["project"],
						"project_name": a.get("project_name") or a["project"],
						"hours": round(float(a["hours"] or 0), 2),
						"notes": a.get("notes") or "",
						"color": _color_for_project(a["project"], color_map),
					}
					for a in day_allocs
				],
				"planned_hours": round(day_planned, 2),
				"free_hours": free_hours,
				"overloaded": day_planned > DEFAULT_DAILY_HOURS,
			}

		weekly_planned = round(sum(d["planned_hours"] for d in days_data.values()), 2)
		weekly_free = round(sum(d["free_hours"] for d in days_data.values()), 2)

		# Project filter: include only if relevant
		if project and not has_project_allocs and weekly_free <= 0:
			continue

		result_employees.append(
			{
				"user": emp["user_id"],
				"full_name": emp["employee_name"],
				"employee": emp_name,
				"daily_capacity_hours": DEFAULT_DAILY_HOURS,
				"weekly_capacity_hours": DEFAULT_DAILY_HOURS * 5,
				"weekly_planned_hours": weekly_planned,
				"weekly_free_hours": weekly_free,
				"has_project_allocs": has_project_allocs,
				"days": days_data,
			}
		)

	# Sort: employees with project allocations first, then alphabetically
	if project:
		result_employees.sort(key=lambda e: (not e["has_project_allocs"], e["full_name"].lower()))
	else:
		result_employees.sort(key=lambda e: e["full_name"].lower())

	return {
		"week_start": week_start_str,
		"week_end": week_end,
		"days": days,
		"daily_capacity_hours": DEFAULT_DAILY_HOURS,
		"project_colors": color_map,
		"employees": result_employees,
	}


def _empty_response(week_start, week_end, days):
	return {
		"week_start": week_start,
		"week_end": week_end,
		"days": days,
		"daily_capacity_hours": DEFAULT_DAILY_HOURS,
		"project_colors": {},
		"employees": [],
	}


@frappe.whitelist()
def get_capacity_projects() -> list[dict]:
	"""Return active projects for the capacity planning project filter."""
	_check_permission()
	return frappe.get_all(
		"Project",
		filters={"status": ["not in", ["Cancelled", "Template"]]},
		fields=["name", "project_name", "status"],
		order_by="project_name",
	)


@frappe.whitelist()
def save_allocation(
	employee: str,
	project: str,
	allocation_date: str,
	hours: float = 8.0,
	notes: str = "",
	name: str | None = None,
) -> dict:
	"""
	Create or update a Project Allocation record.

	Parameters
	----------
	name : str | None
	    Pass the existing record name to update, omit to create.

	Returns
	-------
	dict with ``name``, ``employee``, ``project``, ``allocation_date``, ``hours``
	"""
	_check_permission()

	hours = float(hours) if hours else 0.0

	if _has_doctype("Project Assignment"):
		if name and frappe.db.exists("Project Assignment", name):
			doc = frappe.get_doc("Project Assignment", name)
			doc.project = project
			doc.from_date = allocation_date
			doc.to_date = allocation_date
			doc.hours_per_day = hours
			doc.status = "Active"
			doc.save()
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Project Assignment",
					"employee": employee,
					"project": project,
					"from_date": allocation_date,
					"to_date": allocation_date,
					"hours_per_day": hours,
					"status": "Active",
				}
			)
			doc.insert()
		return {
			"name": doc.name,
			"employee": doc.employee,
			"project": doc.project,
			"allocation_date": str(doc.from_date),
			"hours": doc.hours_per_day,
		}

	if _has_doctype("Project Allocation"):
		if name and frappe.db.exists("Project Allocation", name):
			doc = frappe.get_doc("Project Allocation", name)
			doc.project = project
			doc.allocation_date = allocation_date
			doc.hours = hours
			doc.notes = notes
			doc.save()
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Project Allocation",
					"employee": employee,
					"project": project,
					"allocation_date": allocation_date,
					"hours": hours,
					"notes": notes,
				}
			)
			doc.insert()
		return {
			"name": doc.name,
			"employee": doc.employee,
			"project": doc.project,
			"allocation_date": str(doc.allocation_date),
			"hours": doc.hours,
		}

	frappe.throw(
		_(
			"Capacity Planning is not configured: missing DocType 'Project Assignment' or 'Project Allocation'."
		)
	)


@frappe.whitelist()
def delete_allocation(allocation_name: str) -> dict:
	"""Delete a Project Allocation record."""
	_check_permission()

	if _has_doctype("Project Assignment") and frappe.db.exists("Project Assignment", allocation_name):
		frappe.delete_doc("Project Assignment", allocation_name)
		return {"deleted": allocation_name}

	if _has_doctype("Project Allocation") and frappe.db.exists("Project Allocation", allocation_name):
		frappe.delete_doc("Project Allocation", allocation_name)
		return {"deleted": allocation_name}

	frappe.throw(_("Allocation {0} not found").format(allocation_name))


@frappe.whitelist()
def get_project_employees(project: str) -> list[dict]:
	"""
	Return employees (with user_id) already assigned to this project.
	Useful for pre-populating suggestions in the allocation modal.
	"""
	_check_permission()

	users = frappe.db.sql(
		"""
        SELECT DISTINCT e.name as employee, e.employee_name, e.user_id
        FROM `tabProject User` pu
        JOIN `tabEmployee` e ON e.user_id = pu.user
        WHERE pu.parent = %(project)s
          AND pu.parenttype = 'Project'
          AND e.status = 'Active'
          AND e.user_id IS NOT NULL
        ORDER BY e.employee_name
        """,
		{"project": project},
		as_dict=True,
	)
	return users
