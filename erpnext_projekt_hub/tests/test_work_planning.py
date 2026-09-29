from datetime import date, timedelta

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.api import work_planning
from erpnext_projekt_hub.availability import _as_timedelta, _get_day, get_availability

MONDAY = date(2031, 3, 3)
SATURDAY = MONDAY + timedelta(days=5)


def make_employee(user, **values):
	if not frappe.db.exists("User", user):
		frappe.get_doc(
			{"doctype": "User", "email": user, "first_name": user, "send_welcome_email": 0}
		).insert(ignore_permissions=True)

	employee = frappe.db.get_value("Employee", {"user_id": user})
	if employee:
		frappe.db.set_value("Employee", employee, values)
		return employee

	return (
		frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "_Test Work Planning",
				"company": frappe.db.get_value("Company", {}, "name"),
				"user_id": user,
				"gender": frappe.db.get_value("Gender", {}, "name"),
				"date_of_birth": "1990-05-08",
				"date_of_joining": "2020-01-01",
				"status": "Active",
				**values,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def holiday_list_info(has_weekly_offs=False, from_date=date(2031, 1, 1), to_date=date(2031, 12, 31)):
	return frappe._dict(from_date=from_date, to_date=to_date, has_weekly_offs=has_weekly_offs)


def holiday(description="Holiday", weekly_off=0, is_half_day=0):
	return frappe._dict(description=description, weekly_off=weekly_off, is_half_day=is_half_day)


def leave(from_date, to_date, half_day=0, half_day_date=None, leave_type="Casual Leave"):
	return frappe._dict(
		from_date=from_date,
		to_date=to_date,
		half_day=half_day,
		half_day_date=half_day_date,
		leave_type=leave_type,
	)


def day(on, base_hours=8.0, info=None, holidays=None, leaves=None, employee=None):
	return _get_day(
		on,
		employee or frappe._dict(date_of_joining=date(2020, 1, 1), relieving_date=None),
		base_hours,
		info,
		holidays or {},
		leaves or [],
	)


class TestAvailabilityRules(FrappeTestCase):
	def test_working_day_without_holiday_list_has_the_shift_hours(self):
		result = day(MONDAY, base_hours=7.5)
		self.assertEqual((result["hours"], result["status"]), (7.5, "work"))

	def test_weekend_without_holiday_list_is_off(self):
		self.assertEqual(day(SATURDAY)["status"], "weekend")
		self.assertEqual(day(SATURDAY)["hours"], 0)

	def test_public_holiday_is_off_with_its_name(self):
		result = day(MONDAY, info=holiday_list_info(), holidays={MONDAY: holiday("Easter <b>Monday</b>")})
		self.assertEqual(
			(result["hours"], result["status"], result["reason"]), (0, "holiday", "Easter Monday")
		)

	def test_weekend_is_off_when_the_list_holds_only_public_holidays(self):
		self.assertEqual(day(SATURDAY, info=holiday_list_info(has_weekly_offs=False))["hours"], 0)

	def test_list_with_weekly_offs_decides_about_weekends(self):
		# A six-day week: Saturday isn't a weekly off in the list.
		result = day(SATURDAY, info=holiday_list_info(has_weekly_offs=True))
		self.assertEqual((result["hours"], result["status"]), (8.0, "work"))

	def test_holiday_outside_the_period_of_the_list_is_ignored(self):
		info = holiday_list_info(from_date=date(2030, 1, 1), to_date=date(2030, 12, 31))
		result = day(MONDAY, info=info, holidays={MONDAY: holiday()})
		self.assertEqual(result["hours"], 8.0)

	def test_half_day_holiday_halves_the_day(self):
		result = day(MONDAY, info=holiday_list_info(), holidays={MONDAY: holiday(is_half_day=1)})
		self.assertEqual((result["hours"], result["half_day"]), (4.0, True))

	def test_leave_takes_the_day_off(self):
		result = day(MONDAY, leaves=[leave(MONDAY, MONDAY + timedelta(days=2), leave_type="Casual Leave")])
		self.assertEqual((result["hours"], result["status"], result["reason"]), (0, "leave", "Casual Leave"))

	def test_half_day_leave_halves_only_its_half_day_date(self):
		leaves = [leave(MONDAY, MONDAY + timedelta(days=1), half_day=1, half_day_date=MONDAY)]
		self.assertEqual(day(MONDAY, leaves=leaves)["hours"], 4.0)
		self.assertEqual(day(MONDAY + timedelta(days=1), leaves=leaves)["hours"], 0)

	def test_days_before_joining_are_off(self):
		employee = frappe._dict(date_of_joining=MONDAY + timedelta(days=1), relieving_date=None)
		self.assertEqual(day(MONDAY, employee=employee)["status"], "inactive")
		self.assertEqual(day(MONDAY + timedelta(days=1), employee=employee)["hours"], 8.0)

	def test_shift_times_parse_from_strings(self):
		self.assertEqual(_as_timedelta("07:30:00"), timedelta(hours=7, minutes=30))
		self.assertEqual(_as_timedelta(timedelta(hours=6)), timedelta(hours=6))


class TestWorkPlanning(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		holiday_list = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": "_Test Work Planning 2031",
				"from_date": "2031-01-01",
				"to_date": "2031-12-31",
				# Wednesday of the test week
				"holidays": [{"holiday_date": MONDAY + timedelta(days=2), "description": "_Test Holiday"}],
			}
		).insert(ignore_if_duplicate=True)
		self.employee = make_employee("_test_work_planning@example.com", holiday_list=holiday_list.name)
		self.project = self.make_project("_Test Work Planning Project")
		self.other_project = self.make_project("_Test Work Planning Other Project")
		frappe.db.delete("Work Plan Entry", {"employee": self.employee})

	def tearDown(self):
		frappe.set_user("Administrator")

	@staticmethod
	def make_project(project_name):
		existing = frappe.db.get_value("Project", {"project_name": project_name})
		if existing:
			return existing
		return (
			frappe.get_doc({"doctype": "Project", "project_name": project_name, "status": "Open"})
			.insert()
			.name
		)

	def plan(self, project, *allocations):
		return work_planning.save_plan_entries(
			self.employee,
			project,
			[{"date": str(on), "hours": hours} for on, hours in allocations],
		)

	def test_availability_uses_the_employee_holiday_list(self):
		week = [MONDAY + timedelta(days=offset) for offset in range(7)]
		hours = [get_availability([self.employee], week)[self.employee][str(on)]["hours"] for on in week]
		self.assertEqual(hours, [8.0, 8.0, 0, 8.0, 8.0, 0, 0])

	def test_planning_the_same_project_and_day_again_replaces_its_hours(self):
		self.plan(self.project, (MONDAY, 4))
		self.plan(self.project, (MONDAY, 6))

		entries = frappe.get_all(
			"Work Plan Entry", filters={"employee": self.employee, "date": MONDAY}, pluck="hours"
		)
		self.assertEqual(entries, [6])

	def test_saving_reports_days_planned_above_availability(self):
		self.plan(self.project, (MONDAY, 6))
		result = self.plan(self.other_project, (MONDAY, 4), (MONDAY + timedelta(days=1), 4))

		self.assertEqual(result["overbooked"], [{"date": str(MONDAY), "planned": 10.0, "available": 8.0}])

	def test_work_plan_groups_entries_by_employee_and_day(self):
		self.plan(self.project, (MONDAY, 3))
		self.plan(self.other_project, (MONDAY, 2))

		data = work_planning.get_work_plan(str(MONDAY + timedelta(days=3)))

		self.assertEqual(data["week_start"], str(MONDAY))
		self.assertTrue(data["can_plan"])
		monday = data["plan"][self.employee][str(MONDAY)]
		self.assertEqual(
			sorted((entry.project, entry.hours) for entry in monday),
			sorted([(self.project, 3), (self.other_project, 2)]),
		)

	def test_copy_previous_week_skips_days_off_and_days_already_planned(self):
		previous_monday = MONDAY - timedelta(days=7)
		self.plan(
			self.project,
			(previous_monday, 4),
			(previous_monday + timedelta(days=1), 4),
			(previous_monday + timedelta(days=2), 4),  # Wednesday is a holiday in the test week
		)
		self.plan(self.project, (MONDAY + timedelta(days=1), 2))

		result = work_planning.copy_previous_week(str(MONDAY))

		self.assertEqual(result, {"copied": 1, "skipped_unavailable": 1, "skipped_planned": 1})
		planned = dict(
			frappe.get_all(
				"Work Plan Entry",
				filters={
					"employee": self.employee,
					"date": ("between", [MONDAY, MONDAY + timedelta(days=6)]),
				},
				fields=["date", "hours"],
				as_list=True,
			)
		)
		self.assertEqual(planned, {MONDAY: 4, MONDAY + timedelta(days=1): 2})

	def test_employee_without_planning_rights_sees_only_their_own_plan(self):
		user = "_test_work_planning@example.com"
		frappe.get_doc("User", user).add_roles("Projects User")
		self.plan(self.project, (MONDAY, 3))

		frappe.set_user(user)
		data = work_planning.get_work_plan(str(MONDAY))

		self.assertFalse(data["can_plan"])
		self.assertEqual([row.name for row in data["employees"]], [self.employee])
		self.assertRaises(
			frappe.PermissionError, work_planning.save_plan_entries, self.employee, self.project, []
		)

	def test_duplicate_entry_for_the_same_day_and_project_is_rejected(self):
		self.plan(self.project, (MONDAY, 3))
		entry = frappe.get_doc(
			{
				"doctype": "Work Plan Entry",
				"employee": self.employee,
				"date": MONDAY,
				"project": self.project,
				"hours": 1,
			}
		)
		self.assertRaises(frappe.DuplicateEntryError, entry.insert)
