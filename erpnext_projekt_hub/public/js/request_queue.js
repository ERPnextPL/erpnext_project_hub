// Assignment queues and attachments shared by the Customer Request and Change
// Request forms (see request_queue.py).
frappe.provide("erpnext_projekt_hub.request_queue");

erpnext_projekt_hub.request_queue.setup = function (frm, queue_state) {
	if (frm.is_new()) {
		return;
	}

	if (frm.doc.workflow_state === queue_state) {
		setup_assignment_queue(frm);
	}
	setup_read_only_attachments(frm);
};

function setup_assignment_queue(frm) {
	const isChangeRequest = frm.doctype === "Change Request";
	const assigneeField = isChangeRequest ? "realization_assignee" : "analyst";
	if (!frm.doc[assigneeField]) {
		frm.dashboard.set_headline_alert(
			isChangeRequest
				? __("Waiting for someone to take this for realization, or assign an implementer.")
				: __("Waiting for someone to analyze. Take it, or pick the Assigned Analyst."),
			"yellow"
		);
		frm.add_custom_button(
			isChangeRequest ? __("Take for realization") : __("Take for analysis"),
			() => {
				call_queue(
					frm,
					isChangeRequest ? "take_for_realization" : "take_for_analysis",
					isChangeRequest ? {} : { doctype: frm.doctype }
				);
			}
		).addClass("btn-primary");
		return;
	}

	if (frm.doc[assigneeField] === frappe.session.user) {
		frm.add_custom_button(__("Release"), () => {
			call_queue(
				frm,
				isChangeRequest ? "release_realization" : "release_analysis",
				isChangeRequest ? {} : { doctype: frm.doctype }
			);
		});
	}
}

function call_queue(frm, method, args = {}) {
	return frappe
		.xcall(`erpnext_projekt_hub.request_queue.${method}`, {
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
				call_queue(frm, "attach_file", { doctype: frm.doctype, file_name: file_doc.name });
			},
		});
	});
}
