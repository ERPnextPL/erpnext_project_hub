frappe.ui.form.on("Task", {
	refresh(frm) {
		frm.__status_before_completion = frm.doc.status;
	},

	status(frm) {
		if (frm.doc.status !== "Completed" || frm.is_new()) return;

		const previousStatus = frm.__status_before_completion || "Open";
		frm.disable_save();

		frappe
			.xcall("erpnext_projekt_hub.api.project_hub.get_task_completion_assignees", {
				task_name: frm.doc.name,
			})
			.then((assignees) => {
				if (frm.doc.status !== "Completed") {
					frm.enable_save();
					return;
				}
				const currentUser = frappe.session.user;
				if (
					assignees.length <= 1 ||
					assignees.some((assignee) => assignee.user === currentUser)
				) {
					frm.enable_save();
					return;
				}

				let confirmed = false;
				const dialog = new frappe.ui.Dialog({
					title: __("Who completed this task?"),
					fields: [
						{
							fieldname: "completed_by",
							fieldtype: "Select",
							label: __("Completed by"),
							options: assignees.map((assignee) => ({
								label: assignee.full_name
									? `${assignee.full_name} (${assignee.user})`
									: assignee.user,
								value: assignee.user,
							})),
							reqd: 1,
						},
					],
					primary_action_label: __("Confirm"),
					primary_action(values) {
						if (!values?.completed_by) return;
						confirmed = true;
						frm.set_value("completed_by", values.completed_by).then(() => {
							frm.enable_save();
							dialog.hide();
						});
					},
					secondary_action_label: __("Cancel"),
					secondary_action() {
						dialog.hide();
					},
				});
				dialog.onhide = () => {
					if (!confirmed) frm.set_value("status", previousStatus);
					frm.enable_save();
				};
				dialog.show();
			})
			.catch((error) => {
				if (frm.doc.status !== "Completed") {
					frm.enable_save();
					return;
				}
				frm.set_value("status", previousStatus);
				frm.enable_save();
				frappe.msgprint({
					title: __("Unable to complete task"),
					message: error.message || __("Could not load the task assignees."),
					indicator: "red",
				});
			});
	},
});
