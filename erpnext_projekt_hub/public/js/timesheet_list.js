// Timesheet list with the approval workflow (erpnext_projekt_hub/timesheet_approval.py).
//
// Draft, Pending Approval (orange), Rejected (red) and Cancelled come from the workflow
// state. Approved timesheets keep ERPNext's billing indicator (Billed, Payslip, ...)
// and read "Approved" (green) until they are billed. Approvers get a "To Approve"
// button with the number of timesheets waiting for them.

(() => {
	const WORKFLOW_NAME = "Timesheet Approval";
	const PENDING = "Pending Approval";
	const REJECTED = "Rejected";
	const APPROVED = "Approved";
	const APPROVER_ROLES = ["Timesheet Manager", "Projects Manager"];

	const erpnext_settings = frappe.listview_settings["Timesheet"] || {};
	const billing_indicator = erpnext_settings.get_indicator;

	function uses_approval_workflow(doctype) {
		frappe.workflow.get_state_fieldname(doctype);
		return frappe.workflow.workflows[doctype]?.name === WORKFLOW_NAME;
	}

	function show_state(listview, state) {
		// workflow_state is a standard filter of the list
		const field = listview.page.fields_dict.workflow_state;
		if (field) {
			field.set_value(field.get_value() === state ? "" : state);
		} else {
			listview.filter_area.add([[listview.doctype, "workflow_state", "=", state]]);
		}
	}

	function add_state_buttons(listview) {
		if (!uses_approval_workflow(listview.doctype)) return;

		if (frappe.user.has_role(APPROVER_ROLES)) {
			const label = __("To Approve");
			const $button = listview.page.add_inner_button(label, () =>
				show_state(listview, PENDING)
			);
			frappe.db
				.count(listview.doctype, { filters: { workflow_state: PENDING } })
				.then((count) => {
					if (count) $button.text(`${label} (${count})`);
				});
		}
		listview.page.add_inner_button(__(REJECTED), () => show_state(listview, REJECTED));
	}

	frappe.listview_settings["Timesheet"] = {
		...erpnext_settings,
		add_fields: [
			...new Set([...(erpnext_settings.add_fields || []), "workflow_state", "docstatus"]),
		],
		// Reached for approved timesheets: their workflow state does not override the status.
		get_indicator(doc) {
			const indicator = billing_indicator?.(doc);
			if (indicator) return indicator;
			if (doc.docstatus === 1 && doc.workflow_state === APPROVED) {
				return [__(APPROVED), "green", `workflow_state,=,${APPROVED}`];
			}
		},
		onload(listview) {
			erpnext_settings.onload?.(listview);
			add_state_buttons(listview);
		},
	};
})();
