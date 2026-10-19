// Analysis queue and attachments shared by the Customer Request and Change
// Request forms (see request_queue.py). Requests waiting for analysis are taken
// with "Take for analysis", which records the user in "Assigned Analyst"; a
// manager can also pick the analyst in that field. Once someone is assigned
// the button is gone.
frappe.provide("erpnext_projekt_hub.request_queue");

erpnext_projekt_hub.request_queue.setup = function (frm, analysis_state) {
	if (frm.is_new()) {
		return;
	}

	if (frm.doc.workflow_state === analysis_state) {
		setup_analysis_queue(frm);
	}
	setup_read_only_attachments(frm);
};

function setup_analysis_queue(frm) {
	if (!frm.doc.analyst) {
		frm.dashboard.set_headline_alert(
			__("Waiting for someone to analyze. Take it, or pick the Assigned Analyst."),
			"yellow"
		);
		frm.add_custom_button(__("Take for analysis"), () => {
			call_queue(frm, "take_for_analysis");
		}).addClass("btn-primary");
		return;
	}

	if (frm.doc.analyst === frappe.session.user) {
		frm.add_custom_button(__("Release"), () => {
			call_queue(frm, "release_analysis");
		});
	}
}

function call_queue(frm, method, args = {}) {
	return frappe
		.xcall(`erpnext_projekt_hub.request_queue.${method}`, {
			doctype: frm.doctype,
			name: frm.docname,
			...args,
		})
		.then(() => frm.reload_doc());
}

// The sidebar offers "Attach File" only to users who may edit the request, but
// everyone who can open it may add attachments.
function setup_read_only_attachments(frm) {
	if (frm.has_perm("write")) {
		return;
	}

	frm.add_custom_button(__("Add Attachment"), () => {
		new frappe.ui.FileUploader({
			folder: "Home/Attachments",
			on_success(file_doc) {
				call_queue(frm, "attach_file", { file_name: file_doc.name });
			},
		});
	});
}
