# Copyright (c) 2024, Krzysztof and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class ProjectMilestone(Document):
	def validate(self):
		self.validate_project()
		self.update_statistics()

	def validate_project(self):
		"""Ensure milestone is always linked to a project"""
		if not self.project:
			frappe.throw(_("Project is required for a milestone"))

	def update_statistics(self):
		"""Calculate progress based on linked tasks"""
		if not self.name:
			# New document, skip calculation
			return

		total_tasks = frappe.db.count("Task", {"milestone": self.name})
		completed_tasks = frappe.db.count("Task", {"milestone": self.name, "status": "Completed"})

		self.total_tasks = total_tasks
		self.completed_tasks = completed_tasks

		if total_tasks > 0:
			self.progress = int((completed_tasks / total_tasks) * 100)
		else:
			self.progress = 0

		# Auto-update status based on progress
		if self.status not in ["Completed", "Cancelled"]:
			if self.progress == 100 and total_tasks > 0:
				self.status = "Completed"
			elif self.progress > 0:
				self.status = "In Progress"

	def on_trash(self):
		"""Unlink all tasks when milestone is deleted"""
		frappe.db.set_value("Task", {"milestone": self.name}, "milestone", None)

	def get_health_status(self):
		"""Calculate health status based on deadline and progress"""
		if self.status == "Completed":
			return "completed"

		if self.status == "Cancelled":
			return "cancelled"

		if not self.milestone_date:
			return "no_deadline"

		deadline = getdate(self.milestone_date)
		today_date = getdate(today())

		if deadline < today_date:
			return "overdue"

		from frappe.utils import date_diff

		days_remaining = date_diff(deadline, today_date)

		# At risk if less than 7 days and less than 70% done
		if days_remaining <= 7 and self.progress < 70:
			return "at_risk"

		# At risk if less than 14 days and less than 50% done
		if days_remaining <= 14 and self.progress < 50:
			return "at_risk"

		return "on_track"


def update_milestone_progress(milestone_name):
	"""
	Update milestone progress when a task is updated.
	Called from hooks when Task is saved/deleted.
	"""
	if not milestone_name:
		return

	milestone = frappe.get_doc("Project Milestone", milestone_name)
	milestone.update_statistics()
	milestone.db_update()
