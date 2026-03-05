"""
Unit tests for erpnext_projekt_hub.api.capacity_planning.

Tests cover:
  - Pure helpers: _week_days, _color_for_project
  - Integration: get_capacity_planning_data with mocked frappe DB

Run with:
    cd ~/frappe-bench/apps/erpnext_projekt_hub
    .venv/bin/python -m pytest erpnext_projekt_hub/tests/test_capacity_planning.py -v
"""

import sys
import types
import unittest
from datetime import date
from unittest.mock import MagicMock

# ── Stub `frappe` before any app import ──────────────────────────────────────


def _getdate(value):
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value))


def _whitelist(allow_guest=False):
	def _deco(fn):
		return fn

	return _deco


class _FrappePermissionError(Exception):
	pass


def _throw(msg, exc_type=None):
	raise (exc_type or Exception)(msg)


_frappe = types.ModuleType("frappe")
_frappe.whitelist = _whitelist
_frappe.throw = _throw
_frappe.PermissionError = _FrappePermissionError
_frappe.session = MagicMock()
_frappe.session.user = "admin@example.com"
_frappe.get_roles = MagicMock(return_value=["Projects Manager"])
_frappe.get_all = MagicMock(return_value=[])
_frappe.db = MagicMock()
_frappe.db.sql = MagicMock(return_value=[])
_frappe.log_error = MagicMock()
_frappe._ = lambda x: x

_frappe_utils = types.ModuleType("frappe.utils")
_frappe_utils.getdate = _getdate
_frappe.utils = _frappe_utils

sys.modules["frappe"] = _frappe
sys.modules["frappe.utils"] = _frappe_utils

# ── Import module under test ─────────────────────────────────────────────────

if "erpnext_projekt_hub.api.capacity_planning" in sys.modules:
	del sys.modules["erpnext_projekt_hub.api.capacity_planning"]

import erpnext_projekt_hub.api.capacity_planning as _cp

_cp.frappe = _frappe
_cp.getdate = _getdate

from erpnext_projekt_hub.api.capacity_planning import (
	DEFAULT_DAILY_HOURS,
	_color_for_project,
	_week_days,
	get_capacity_planning_data,
	save_allocation,
)

# ── Tiny _dict helper ─────────────────────────────────────────────────────────


class _dict(dict):
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError as exc:
			raise AttributeError(key) from exc

	def __setattr__(self, key, value):
		self[key] = value

	def get(self, key, default=None):
		return super().get(key, default)


# ── Fixture builders ──────────────────────────────────────────────────────────


def _emp(name, full_name, user_id):
	return _dict(name=name, employee_name=full_name, user_id=user_id)


def _alloc(name, employee, project, alloc_date, hours=8.0, project_name=None, notes=""):
	return _dict(
		name=name,
		employee=employee,
		project=project,
		allocation_date=date.fromisoformat(alloc_date),
		hours=hours,
		project_name=project_name or f"Project {project}",
		notes=notes,
	)


# ═════════════════════════════════════════════════════════════════════════════
# 1. Pure helpers
# ═════════════════════════════════════════════════════════════════════════════


class TestWeekDays(unittest.TestCase):
	def test_five_days(self):
		self.assertEqual(len(_week_days("2025-03-03")), 5)

	def test_monday_start(self):
		self.assertEqual(_week_days("2025-03-03")[0], "2025-03-03")

	def test_friday_end(self):
		self.assertEqual(_week_days("2025-03-03")[-1], "2025-03-07")

	def test_consecutive(self):
		days = _week_days("2025-03-03")
		for i in range(1, 5):
			self.assertEqual((date.fromisoformat(days[i]) - date.fromisoformat(days[i - 1])).days, 1)


class TestColorForProject(unittest.TestCase):
	def test_returns_dict_with_bg_and_text(self):
		cm = {}
		color = _color_for_project("PROJ-001", cm)
		self.assertIn("bg", color)
		self.assertIn("text", color)

	def test_stable_across_calls(self):
		cm = {}
		c1 = _color_for_project("PROJ-001", cm)
		c2 = _color_for_project("PROJ-001", cm)
		self.assertEqual(c1, c2)

	def test_different_projects_get_different_colors(self):
		cm = {}
		c1 = _color_for_project("PROJ-001", cm)
		c2 = _color_for_project("PROJ-002", cm)
		self.assertNotEqual(c1, c2)

	def test_wraps_around_palette(self):
		cm = {}
		# Register more projects than palette length (12)
		for i in range(15):
			_color_for_project(f"PROJ-{i:03}", cm)
		# No KeyError — palette wraps
		self.assertEqual(len(cm), 15)


class TestDefaultCapacity(unittest.TestCase):
	def test_positive(self):
		self.assertGreater(DEFAULT_DAILY_HOURS, 0)

	def test_value(self):
		self.assertEqual(DEFAULT_DAILY_HOURS, 8.0)


# ═════════════════════════════════════════════════════════════════════════════
# 2. get_capacity_planning_data — mocked DB
# ═════════════════════════════════════════════════════════════════════════════


class TestGetCapacityPlanningData(unittest.TestCase):
	def setUp(self):
		_frappe.session.user = "admin@example.com"
		_frappe.get_roles = MagicMock(return_value=["Projects Manager"])
		_frappe.get_all = MagicMock(return_value=[])
		_frappe.db.sql = MagicMock(return_value=[])
		_frappe.throw = _throw
		_cp.frappe = _frappe

	# ── basic ─────────────────────────────────────────────────────────────

	def test_no_employees_returns_empty(self):
		result = get_capacity_planning_data("2025-03-03")
		self.assertEqual(result["employees"], [])
		self.assertEqual(len(result["days"]), 5)
		self.assertIn("project_colors", result)

	def test_employee_no_allocations_still_in_results(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		result = get_capacity_planning_data("2025-03-03")
		self.assertEqual(len(result["employees"]), 1)
		emp = result["employees"][0]
		self.assertEqual(emp["weekly_planned_hours"], 0)
		self.assertEqual(emp["weekly_free_hours"], DEFAULT_DAILY_HOURS * 5)

	# ── allocation in cell ────────────────────────────────────────────────

	def test_allocation_appears_in_correct_day_cell(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4)]
		result = get_capacity_planning_data("2025-03-03")
		emp = result["employees"][0]
		monday = result["days"][0]
		self.assertEqual(len(emp["days"][monday]["allocations"]), 1)
		self.assertEqual(emp["days"][monday]["allocations"][0]["project"], "PROJ-1")
		self.assertAlmostEqual(emp["days"][monday]["planned_hours"], 4.0)
		self.assertAlmostEqual(emp["days"][monday]["free_hours"], 4.0)

	def test_allocation_not_in_wrong_day(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4)]
		result = get_capacity_planning_data("2025-03-03")
		emp = result["employees"][0]
		tuesday = result["days"][1]
		self.assertEqual(emp["days"][tuesday]["allocations"], [])

	def test_multiple_projects_same_day(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [
			_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4),
			_alloc("PA-002", "EMP-001", "PROJ-2", "2025-03-03", 3),
		]
		result = get_capacity_planning_data("2025-03-03")
		emp = result["employees"][0]
		monday = result["days"][0]
		self.assertEqual(len(emp["days"][monday]["allocations"]), 2)
		self.assertAlmostEqual(emp["days"][monday]["planned_hours"], 7.0)
		self.assertAlmostEqual(emp["days"][monday]["free_hours"], 1.0)

	# ── overload ──────────────────────────────────────────────────────────

	def test_overload_flag_when_more_than_daily_capacity(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [
			_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 5),
			_alloc("PA-002", "EMP-001", "PROJ-2", "2025-03-03", 5),
		]
		result = get_capacity_planning_data("2025-03-03")
		monday = result["days"][0]
		self.assertTrue(result["employees"][0]["days"][monday]["overloaded"])

	def test_no_overload_at_exactly_capacity(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 8)]
		result = get_capacity_planning_data("2025-03-03")
		monday = result["days"][0]
		self.assertFalse(result["employees"][0]["days"][monday]["overloaded"])

	# ── project filter ────────────────────────────────────────────────────

	def test_project_filter_includes_employee_with_allocation(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4)]
		result = get_capacity_planning_data("2025-03-03", project="PROJ-1")
		self.assertEqual(len(result["employees"]), 1)
		self.assertTrue(result["employees"][0]["has_project_allocs"])

	def test_project_filter_includes_free_employee(self):
		_frappe.get_all.return_value = [
			_emp("EMP-001", "Jan Kowalski", "jan@x.com"),
			_emp("EMP-002", "Anna Nowak", "anna@x.com"),
		]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4)]
		# Anna has no allocations → she has free capacity → included
		result = get_capacity_planning_data("2025-03-03", project="PROJ-1")
		users = [e["user"] for e in result["employees"]]
		self.assertIn("anna@x.com", users)

	def test_project_filter_excludes_fully_booked_unrelated(self):
		_frappe.get_all.return_value = [
			_emp("EMP-001", "Jan Kowalski", "jan@x.com"),
			_emp("EMP-002", "Anna Nowak", "anna@x.com"),
		]
		# Anna is fully booked (8h/day x 5) on PROJ-2, no time left
		week_allocs = [_alloc(f"PA-A-{i}", "EMP-002", "PROJ-2", f"2025-03-0{i+3}", 8) for i in range(5)]
		# Fix dates (Fri would be 2025-03-07, not 2025-03-08):
		week_allocs = [
			_alloc("PA-A-0", "EMP-002", "PROJ-2", "2025-03-03", 8),
			_alloc("PA-A-1", "EMP-002", "PROJ-2", "2025-03-04", 8),
			_alloc("PA-A-2", "EMP-002", "PROJ-2", "2025-03-05", 8),
			_alloc("PA-A-3", "EMP-002", "PROJ-2", "2025-03-06", 8),
			_alloc("PA-A-4", "EMP-002", "PROJ-2", "2025-03-07", 8),
			_alloc("PA-J-0", "EMP-001", "PROJ-1", "2025-03-03", 4),
		]
		_frappe.db.sql.return_value = week_allocs
		result = get_capacity_planning_data("2025-03-03", project="PROJ-1")
		users = [e["user"] for e in result["employees"]]
		self.assertIn("jan@x.com", users)
		self.assertNotIn("anna@x.com", users)

	# ── sorting ───────────────────────────────────────────────────────────

	def test_sorted_alphabetically_without_filter(self):
		_frappe.get_all.return_value = [
			_emp("EMP-002", "Zenon Malinowski", "zenon@x.com"),
			_emp("EMP-001", "Anna Nowak", "anna@x.com"),
		]
		result = get_capacity_planning_data("2025-03-03")
		names = [e["full_name"] for e in result["employees"]]
		self.assertEqual(names, sorted(names, key=str.lower))

	def test_project_employees_sorted_first(self):
		_frappe.get_all.return_value = [
			_emp("EMP-001", "Anna Nowak", "anna@x.com"),
			_emp("EMP-002", "Zenon Malinowski", "zenon@x.com"),
		]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-002", "PROJ-1", "2025-03-03", 4)]
		result = get_capacity_planning_data("2025-03-03", project="PROJ-1")
		self.assertEqual(result["employees"][0]["user"], "zenon@x.com")

	# ── permissions ───────────────────────────────────────────────────────

	def test_permission_denied_for_employee_role(self):
		_frappe.get_roles = MagicMock(return_value=["Employee"])
		with self.assertRaises(Exception):
			get_capacity_planning_data("2025-03-03")

	def test_project_manager_role_allowed(self):
		_frappe.get_roles = MagicMock(return_value=["Project Manager"])
		result = get_capacity_planning_data("2025-03-03")
		self.assertIn("employees", result)

	def test_team_lead_role_allowed(self):
		_frappe.get_roles = MagicMock(return_value=["Team Lead"])
		result = get_capacity_planning_data("2025-03-03")
		self.assertIn("employees", result)

	# ── project_colors in response ────────────────────────────────────────

	def test_project_colors_in_response(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4)]
		result = get_capacity_planning_data("2025-03-03")
		self.assertIn("PROJ-1", result["project_colors"])
		color = result["project_colors"]["PROJ-1"]
		self.assertIn("bg", color)
		self.assertIn("text", color)

	def test_allocation_chip_contains_color(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4)]
		result = get_capacity_planning_data("2025-03-03")
		alloc = result["employees"][0]["days"]["2025-03-03"]["allocations"][0]
		self.assertIn("color", alloc)
		self.assertIn("bg", alloc["color"])

	# ── AND filter ─────────────────────────────────────────────────────────

	def test_and_filter_employee_plus_project(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4)]
		result = get_capacity_planning_data("2025-03-03", project="PROJ-1", employee_user="jan@x.com")
		self.assertEqual(len(result["employees"]), 1)
		self.assertEqual(result["employees"][0]["user"], "jan@x.com")

	# ── weekly totals ──────────────────────────────────────────────────────

	def test_weekly_planned_hours_sum(self):
		_frappe.get_all.return_value = [_emp("EMP-001", "Jan Kowalski", "jan@x.com")]
		_frappe.db.sql.return_value = [
			_alloc("PA-001", "EMP-001", "PROJ-1", "2025-03-03", 4),
			_alloc("PA-002", "EMP-001", "PROJ-1", "2025-03-04", 6),
		]
		result = get_capacity_planning_data("2025-03-03")
		emp = result["employees"][0]
		self.assertAlmostEqual(emp["weekly_planned_hours"], 10.0)
		self.assertAlmostEqual(emp["weekly_free_hours"], DEFAULT_DAILY_HOURS * 5 - 10.0)


class TestSaveAllocationValidation(unittest.TestCase):
	def setUp(self):
		_frappe.session.user = "admin@example.com"
		_frappe.get_roles = MagicMock(return_value=["Projects Manager"])
		_frappe.throw = _throw
		_cp.frappe = _frappe

	def test_rejects_negative_hours(self):
		with self.assertRaises(Exception):
			save_allocation(
				employee="EMP-001",
				project="PROJ-001",
				allocation_date="2025-03-03",
				hours=-1,
			)


if __name__ == "__main__":
	unittest.main()
