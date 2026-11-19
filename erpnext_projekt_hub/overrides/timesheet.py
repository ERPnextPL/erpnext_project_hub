import frappe
from erpnext.projects.doctype.timesheet.timesheet import Timesheet


class HubTimesheet(Timesheet):
	"""Timesheet controller tweaks, wired in hooks.py like ``HubTask``."""

	def update_task_and_project(self):
		"""Refresh task and project totals without touching the task status.

		ERPNext derives the status from submitted time logs on every submit,
		cancel and approval: no logs reopens the task as Open, any log makes it
		Working. That wipes out statuses the Hub sets itself (Pending Review,
		Completed, ...), so only the logged time and costing are recomputed here.
		"""
		tasks, projects = [], []

		for data in self.time_logs:
			if data.task and data.task not in tasks:
				task = frappe.get_doc("Task", data.task)
				task.update_time_and_costing()
				task.save(ignore_permissions=True)
				tasks.append(data.task)

			if data.project and data.project not in projects:
				projects.append(data.project)

		for project in projects:
			project_doc = frappe.get_doc("Project", project)
			project_doc.update_project()
			project_doc.save(ignore_permissions=True)

		self.calculate_total_amounts()
		self.calculate_percentage_billed()
		self.set_status()
