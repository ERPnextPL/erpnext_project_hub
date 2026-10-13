frappe.ui.form.on("Customer Request", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.workflow_state === "To Analyze") {
			setup_analysis_queue(frm);
		}

		if (
			frm.doc.docstatus === 0 &&
			frm.doc.workflow_state === "Accepted" &&
			!frm.doc.change_request
		) {
			frm.add_custom_button(__("Create Change Request"), () => {
				frm.call("create_change_request").then((r) => {
					if (!r.message) {
						return;
					}

					frappe.show_alert({
						message: __("Change Request created"),
						indicator: "green",
					});
					frm.reload_doc();
				});
			});
		}
	},
});

// Requests waiting for analysis form a queue: anyone free takes one with
// "Take for analysis", and a manager can assign a developer from the
// "Assigned To" sidebar. The assignment closes once the request leaves analysis.
function setup_analysis_queue(frm) {
	const assignees = JSON.parse(frm.doc._assign || "[]");

	if (!assignees.length) {
		frm.dashboard.set_headline_alert(
			__("Waiting for someone to analyze. Take it, or assign a developer in the sidebar."),
			"yellow"
		);
	}

	if (assignees.includes(frappe.session.user)) {
		frm.add_custom_button(__("Release"), () => {
			frappe
				.xcall("frappe.desk.form.assign_to.remove", {
					doctype: frm.doctype,
					name: frm.docname,
					assign_to: frappe.session.user,
				})
				.then(() => frm.reload_doc());
		});
		return;
	}

	frm.add_custom_button(__("Take for analysis"), () => {
		frappe
			.xcall("frappe.desk.form.assign_to.add", {
				doctype: frm.doctype,
				name: frm.docname,
				assign_to: [frappe.session.user],
				description: frm.doc.subject,
			})
			.then(() => frm.reload_doc());
	}).addClass("btn-primary");
}
