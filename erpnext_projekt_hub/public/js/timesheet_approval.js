// Timesheet approval in the desk form (workflow "Timesheet Approval", see
// erpnext_projekt_hub/timesheet_approval.py): a coloured message says what the
// approval state means and who acts next, and "Reject" asks for the reason.

(() => {
	const WORKFLOW_NAME = "Timesheet Approval";
	const DRAFT = "Draft";
	const PENDING = "Pending Approval";
	const APPROVED = "Approved";
	const REJECTED = "Rejected";
	const REJECT = "Reject";
	// Approve and reject the hours of others; admins have full rights, their own hours too.
	const APPROVER_ROLES = ["Timesheet Manager", "Projects Manager", "Project Manager"];
	const ADMIN_ROLES = ["System Manager"];

	function uses_approval_workflow(frm) {
		frappe.workflow.get_state_fieldname(frm.doctype);
		return frappe.workflow.workflows[frm.doctype]?.name === WORKFLOW_NAME;
	}

	// The full name even for the current user (frappe.user.full_name says "You").
	function user_name(user) {
		return frappe.utils.escape_html(user ? frappe.user_info(user).fullname || user : "");
	}

	function when(value) {
		return value ? frappe.datetime.str_to_user(value) : "";
	}

	function action_hint(action) {
		return __("use {0} → {1}", [`<b>${__("Actions")}</b>`, `<b>${__(action)}</b>`]);
	}

	function show_approval_message(frm) {
		frm.set_intro("");
		if (frm.is_new() || !uses_approval_workflow(frm)) return;

		const doc = frm.doc;
		const user = frappe.session.user;
		const is_admin = user === "Administrator" || frappe.user.has_role(ADMIN_ROLES);
		// Timesheet.user is the employee's user (ERPNext keeps it set), else the creator.
		const is_author = user === (doc.user || doc.owner);
		const is_own = is_author || user === doc.owner;
		const reviews_this = is_admin || (frappe.user.has_role(APPROVER_ROLES) && !is_own);

		if (doc.workflow_state === DRAFT) {
			frm.set_intro(
				__(
					"Draft: when the hours are complete, {0}. Hours count towards project costs, invoices and payroll only after approval.",
					[action_hint("Send for Approval")]
				),
				"blue"
			);
		} else if (doc.workflow_state === PENDING) {
			const since = when(doc.approval_requested_on);
			let message;
			if (reviews_this) {
				message = __("Waiting for approval since {0}. Check the hours, then {1} or {2}.", [
					since,
					action_hint("Approve"),
					`<b>${__(REJECT)}</b>`,
				]);
			} else {
				message = __(
					"Sent for approval on {0}. The hours are locked until the approver decides.",
					[since]
				);
				if (is_author) {
					message += ` ${__("To correct them first, {0}.", [action_hint("Withdraw")])}`;
				}
				if (is_own && frappe.user.has_role(APPROVER_ROLES)) {
					// Approvers may edit pending timesheets of others, not their own (the
					// server refuses it too); "Withdraw" stays in the Actions menu.
					frm.disable_form();
					message += `<div class="mt-2">${__(
						"You do not approve your own hours; another approver reviews them."
					)}</div>`;
				}
			}
			frm.set_intro(message, "orange");
		} else if (doc.workflow_state === REJECTED) {
			const reason = frappe.utils
				.escape_html(doc.rejection_reason || "")
				.replace(/\n/g, "<br>");
			frm.set_intro(
				`${__("Rejected by {0} on {1}.", [
					user_name(doc.reviewed_by),
					when(doc.reviewed_on),
				])}
				<div class="mt-2"><b>${__("Rejection Reason")}:</b> ${reason}</div>
				<div class="mt-2">${__("Correct the hours, then {0}.", [action_hint("Resubmit")])}</div>`,
				"red"
			);
		} else if (doc.workflow_state === APPROVED && doc.reviewed_by) {
			frm.set_intro(
				__("Approved by {0} on {1}.", [user_name(doc.reviewed_by), when(doc.reviewed_on)]),
				"green"
			);
		}
	}

	// The standard action reloads the timesheet from the database before it applies the
	// transition, so the reason is sent with a dedicated call that stores it and rejects.
	function ask_rejection_reason(frm) {
		// The workflow froze the page before calling us; the dialog must stay usable.
		frappe.dom.unfreeze();
		frm.selected_workflow_action = null;

		// Never resolves: the standard transition must not run, the dialog does the work.
		return new Promise(() => {
			const dialog = new frappe.ui.Dialog({
				title: __("Reject timesheet {0}", [frm.doc.name]),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "help",
						options: `<p class="text-muted">${__(
							"The employee sees this reason, corrects the hours and sends the timesheet again."
						)}</p>`,
					},
					{
						fieldtype: "Small Text",
						fieldname: "reason",
						label: __("Rejection Reason"),
						reqd: 1,
					},
				],
				primary_action_label: __(REJECT),
				primary_action(values) {
					const reason = (values.reason || "").trim();
					if (!reason) {
						frappe.msgprint(__("Please enter the reason for rejection."));
						return;
					}
					dialog.disable_primary_action();
					frappe
						.call({
							method: "erpnext_projekt_hub.timesheet_approval.reject_timesheet",
							args: { timesheet: frm.doc.name, reason },
							freeze: true,
							freeze_message: __("Rejecting..."),
						})
						.then(() => {
							dialog.hide();
							frappe.show_alert({
								message: __("Timesheet rejected"),
								indicator: "red",
							});
							frm.reload_doc();
						})
						.always(() => dialog.enable_primary_action());
				},
			});
			dialog.show();
			dialog.fields_dict.reason.$input?.trigger("focus");
		});
	}

	frappe.ui.form.on("Timesheet", {
		refresh(frm) {
			show_approval_message(frm);
		},
		before_workflow_action(frm) {
			if (uses_approval_workflow(frm) && frm.selected_workflow_action === REJECT) {
				return ask_rejection_reason(frm);
			}
		},
	});
})();
