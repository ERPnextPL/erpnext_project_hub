// Project doctype customization - adds "Open Project Hub" button
frappe.ui.form.on("Project", {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Open Project Hub"),
				function () {
					window.open(`/project-hub/${frm.doc.name}`, "_blank");
				},
				__("View")
			);
		}
	},
});
