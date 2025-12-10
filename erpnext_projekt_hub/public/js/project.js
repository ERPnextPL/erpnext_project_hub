// Project doctype customization - adds "Open Outliner" button
frappe.ui.form.on("Project", {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Open Outliner"),
				function () {
					window.open(`/outliner/${frm.doc.name}`, "_blank");
				},
				__("View")
			);
		}
	},
});
