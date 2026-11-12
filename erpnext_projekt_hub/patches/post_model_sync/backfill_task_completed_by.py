import frappe


def execute():
	frappe.db.sql(
		"""
		UPDATE `tabTask` task
		INNER JOIN (
			SELECT reference_name, MIN(allocated_to) AS allocated_to
			FROM `tabToDo`
			WHERE reference_type = 'Task'
				AND status = 'Closed'
				AND allocated_to IS NOT NULL
			GROUP BY reference_name
			HAVING COUNT(DISTINCT allocated_to) = 1
		) assignment ON assignment.reference_name = task.name
		SET task.completed_by = assignment.allocated_to
		WHERE task.status = 'Completed'
			AND (task.completed_by IS NULL OR task.completed_by = '')
		"""
	)
	frappe.clear_cache(doctype="Task")
