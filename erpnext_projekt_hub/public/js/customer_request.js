frappe.ui.form.on("Customer Request", {
	refresh(frm) {
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
