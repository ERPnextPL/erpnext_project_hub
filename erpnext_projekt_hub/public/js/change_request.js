frappe.ui.form.on("Change Request", {
	refresh(frm) {
		// Assign a realization owner while the request is awaiting approval.
		erpnext_projekt_hub.request_queue.setup(frm, "Draft");
		frm.set_df_property("realization_assignee", "read_only", Boolean(frm.doc.task));
	},
});
