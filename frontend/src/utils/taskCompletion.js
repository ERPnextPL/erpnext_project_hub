import { getRealWindow, translate } from "./translation";

export async function promptForCompletionAssignee(taskName) {
	const win = getRealWindow();
	const frappe = win?.frappe;
	if (!frappe?.xcall || !frappe.ui?.Dialog) {
		throw new Error(translate("Task completion requires the Frappe dialog interface."));
	}

	const assignees = await frappe.xcall(
		"erpnext_projekt_hub.api.project_hub.get_task_completion_assignees",
		{ task_name: taskName }
	);
	const currentUser = frappe.session?.user;
	if (
		assignees.length <= 1 ||
		assignees.some((assignee) => assignee.user === currentUser)
	) {
		return undefined;
	}

	return new Promise((resolve) => {
		let settled = false;
		let dialog;
		const finish = (value) => {
			if (settled) return;
			settled = true;
			resolve(value);
			dialog?.hide();
		};

		dialog = new frappe.ui.Dialog({
			title: translate("Who completed this task?"),
			fields: [
				{
					fieldname: "completed_by",
					fieldtype: "Select",
					label: translate("Completed by"),
					options: assignees.map((assignee) => ({
						label: assignee.full_name
							? `${assignee.full_name} (${assignee.user})`
							: assignee.user,
						value: assignee.user,
					})),
					reqd: 1,
				},
			],
			primary_action_label: translate("Confirm"),
			primary_action(values) {
				if (values?.completed_by) finish(values.completed_by);
			},
			secondary_action_label: translate("Cancel"),
			secondary_action() {
				finish(null);
			},
		});
		dialog.onhide = () => {
			if (!settled) {
				settled = true;
				resolve(null);
			}
		};
		dialog.show();
	});
}
