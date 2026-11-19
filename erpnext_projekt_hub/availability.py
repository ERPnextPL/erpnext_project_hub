"""Daily working time available to employees, read from what HR has set up in the system.

For every employee and day:

- the base hours come from the employee's shift: an active HRMS Shift Assignment
  covering the day, else the employee's default shift. Without a shift the base is
  DEFAULT_DAILY_HOURS;
- a day in the employee's holiday list (the employee's own list, else the company's
  default) is off, a half-day holiday halves it. Saturday and Sunday are off too,
  unless the holiday list covers the day and sets the weekly offs itself (many lists
  only hold public holidays);
- approved leave takes the day off, or half of it for a half-day leave;
- days before the employee joined or after they were relieved are off.

The HRMS parts (shifts, leave) are skipped on sites without HRMS.
"""

from collections import defaultdict
from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import flt, getdate, strip_html

DEFAULT_DAILY_HOURS = 8.0

# Day statuses the frontend knows how to label.
WORK = "work"
WEEKEND = "weekend"
HOLIDAY = "holiday"
LEAVE = "leave"
INACTIVE = "inactive"


def get_availability(employees: list[str], dates: list[date]) -> dict[str, dict[str, dict]]:
	"""Return the availability of each employee on each date.

	{employee: {"YYYY-MM-DD": {"hours", "base_hours", "status", "reason", "half_day"}}}
	`hours` is what can be planned that day, `base_hours` a full working day.
	"""
	if not employees or not dates:
		return {}

	dates = sorted(getdate(d) for d in dates)
	start, end = dates[0], dates[-1]

	employee_rows = _get_employees(employees)
	holiday_lists = _get_holiday_lists(employee_rows)
	holidays = _get_holidays(set(holiday_lists.values()), start, end)
	list_info = _get_holiday_list_info(set(holiday_lists.values()))
	shifts = _ShiftHours(employee_rows, start, end)
	leaves = _get_leaves(employees, start, end)

	availability = {}
	for employee in employees:
		row = employee_rows.get(employee)
		if not row:
			continue

		holiday_list = holiday_lists.get(employee)
		days = {}
		for day in dates:
			days[str(day)] = _get_day(
				day,
				row,
				shifts.get(employee, day),
				list_info.get(holiday_list),
				holidays.get(holiday_list, {}),
				leaves.get(employee, []),
			)
		availability[employee] = days

	return availability


def _get_day(day, employee, base_hours, holiday_list_info, holidays, leaves) -> dict:
	result = {"hours": 0.0, "base_hours": base_hours, "status": WORK, "reason": None, "half_day": False}

	joined = employee.get("date_of_joining")
	relieved = employee.get("relieving_date")
	if (joined and day < getdate(joined)) or (relieved and day > getdate(relieved)):
		result["status"] = INACTIVE
		return result

	share = 1.0
	list_covers_day = bool(
		holiday_list_info and holiday_list_info.from_date <= day <= holiday_list_info.to_date
	)
	holiday = holidays.get(day) if list_covers_day else None
	if holiday:
		result["status"] = WEEKEND if holiday.weekly_off else HOLIDAY
		result["reason"] = strip_html(holiday.description or "").strip() or None
		if not holiday.get("is_half_day"):
			return result
		share -= 0.5
		result["half_day"] = True
	elif day.weekday() >= 5 and not (list_covers_day and holiday_list_info.has_weekly_offs):
		result["status"] = WEEKEND
		return result

	leave = next((leave for leave in leaves if leave.from_date <= day <= leave.to_date), None)
	if leave:
		result["status"] = LEAVE
		result["reason"] = _(leave.leave_type)
		if _is_half_day_leave(leave, day):
			share -= 0.5
			result["half_day"] = True
		else:
			share = 0.0

	result["hours"] = flt(base_hours * max(share, 0.0), 2)
	return result


def _is_half_day_leave(leave, day) -> bool:
	if not leave.half_day:
		return False
	if leave.half_day_date:
		return getdate(leave.half_day_date) == day
	return leave.from_date == leave.to_date


def _get_employees(employees: list[str]) -> dict[str, dict]:
	fields = ["name", "company", "holiday_list", "date_of_joining", "relieving_date"]
	if frappe.get_meta("Employee").has_field("default_shift"):
		fields.append("default_shift")

	return {
		row.name: row
		for row in frappe.get_all("Employee", filters={"name": ("in", employees)}, fields=fields)
	}


def _get_holiday_lists(employee_rows: dict[str, dict]) -> dict[str, str]:
	"""Map each employee to their holiday list: their own, else their company's default."""
	companies = {row.company for row in employee_rows.values() if row.company and not row.holiday_list}
	company_lists = {}
	if companies:
		company_lists = dict(
			frappe.get_all(
				"Company",
				filters={"name": ("in", list(companies))},
				fields=["name", "default_holiday_list"],
				as_list=True,
			)
		)

	holiday_lists = {}
	for employee, row in employee_rows.items():
		holiday_list = row.holiday_list or company_lists.get(row.company)
		if holiday_list:
			holiday_lists[employee] = holiday_list
	return holiday_lists


def _get_holiday_list_info(holiday_lists: set[str]) -> dict[str, dict]:
	"""Period each holiday list covers, and whether it lists the weekly offs."""
	if not holiday_lists:
		return {}

	with_weekly_offs = set(
		frappe.get_all(
			"Holiday",
			filters={"parenttype": "Holiday List", "parent": ("in", list(holiday_lists)), "weekly_off": 1},
			pluck="parent",
			distinct=True,
		)
	)

	info = {}
	for row in frappe.get_all(
		"Holiday List",
		filters={"name": ("in", list(holiday_lists))},
		fields=["name", "from_date", "to_date"],
	):
		if row.from_date and row.to_date:
			info[row.name] = frappe._dict(
				from_date=getdate(row.from_date),
				to_date=getdate(row.to_date),
				has_weekly_offs=row.name in with_weekly_offs,
			)
	return info


def _get_holidays(holiday_lists: set[str], start: date, end: date) -> dict[str, dict[date, dict]]:
	if not holiday_lists:
		return {}

	fields = ["parent", "holiday_date", "description", "weekly_off"]
	if frappe.get_meta("Holiday").has_field("is_half_day"):
		fields.append("is_half_day")

	holidays = defaultdict(dict)
	for row in frappe.get_all(
		"Holiday",
		filters={
			"parenttype": "Holiday List",
			"parent": ("in", list(holiday_lists)),
			"holiday_date": ("between", [start, end]),
		},
		fields=fields,
	):
		holidays[row.parent][getdate(row.holiday_date)] = row
	return holidays


def _get_leaves(employees: list[str], start: date, end: date) -> dict[str, list]:
	if not frappe.db.exists("DocType", "Leave Application"):
		return {}

	leaves = defaultdict(list)
	for row in frappe.get_all(
		"Leave Application",
		filters={
			"employee": ("in", employees),
			"docstatus": 1,
			"status": "Approved",
			"from_date": ("<=", end),
			"to_date": (">=", start),
		},
		fields=["employee", "leave_type", "from_date", "to_date", "half_day", "half_day_date"],
	):
		row.from_date, row.to_date = getdate(row.from_date), getdate(row.to_date)
		leaves[row.employee].append(row)
	return leaves


class _ShiftHours:
	"""Length of the shift each employee works on a given day."""

	def __init__(self, employee_rows: dict[str, dict], start: date, end: date):
		self.default_shifts = {
			employee: row.default_shift for employee, row in employee_rows.items() if row.get("default_shift")
		}
		self.assignments = self._get_assignments(list(employee_rows), start, end)

		shift_types = set(self.default_shifts.values())
		for rows in self.assignments.values():
			shift_types.update(row.shift_type for row in rows)
		self.shift_hours = self._get_shift_hours(shift_types)

	def get(self, employee: str, day: date) -> float:
		assignment = next(
			(
				row
				for row in self.assignments.get(employee, [])
				if row.start_date <= day and (not row.end_date or day <= row.end_date)
			),
			None,
		)
		shift_type = assignment.shift_type if assignment else self.default_shifts.get(employee)
		return self.shift_hours.get(shift_type) or DEFAULT_DAILY_HOURS

	@staticmethod
	def _get_assignments(employees: list[str], start: date, end: date) -> dict[str, list]:
		if not employees or not frappe.db.exists("DocType", "Shift Assignment"):
			return {}

		assignments = defaultdict(list)
		for row in frappe.get_all(
			"Shift Assignment",
			filters={
				"employee": ("in", employees),
				"docstatus": 1,
				"status": "Active",
				"start_date": ("<=", end),
			},
			or_filters=[["end_date", "is", "not set"], ["end_date", ">=", start]],
			fields=["employee", "shift_type", "start_date", "end_date"],
			order_by="start_date desc",
		):
			row.start_date = getdate(row.start_date)
			row.end_date = getdate(row.end_date) if row.end_date else None
			assignments[row.employee].append(row)
		return assignments

	@staticmethod
	def _get_shift_hours(shift_types: set[str]) -> dict[str, float]:
		shift_types.discard(None)
		if not shift_types or not frappe.db.exists("DocType", "Shift Type"):
			return {}

		hours = {}
		for row in frappe.get_all(
			"Shift Type",
			filters={"name": ("in", list(shift_types))},
			fields=["name", "start_time", "end_time"],
		):
			if row.start_time is None or row.end_time is None:
				continue
			length = _as_timedelta(row.end_time) - _as_timedelta(row.start_time)
			if length <= timedelta(0):
				length += timedelta(days=1)  # overnight shift
			hours[row.name] = flt(length.total_seconds() / 3600, 2)
		return hours


def _as_timedelta(value) -> timedelta:
	if isinstance(value, timedelta):
		return value
	hours, minutes, *seconds = str(value).split(":")
	return timedelta(hours=int(hours), minutes=int(minutes), seconds=float(seconds[0]) if seconds else 0)
