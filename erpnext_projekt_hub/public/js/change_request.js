frappe.ui.form.on("Change Request", {
	refresh(frm) {
		// A Change Request is analyzed while it is still a draft.
		erpnext_projekt_hub.request_queue.setup(frm, "Draft");
	},
});
