// Override ERPNext timer functionality to add custom defaults and ESC key handling
// This file extends the standard timer.js without modifying ERPNext core files

const erpnext = frappe.erpnext ?? window.erpnext ?? {};

frappe.provide("erpnext.timesheet");

// Store original timer function
const original_timer = erpnext.timesheet?.timer;

erpnext.timesheet.timer = function (frm, row, timestamp = 0) {
	let dialog = new frappe.ui.Dialog({
		title: __("Timer"),
		fields: [
			{
				fieldtype: "Link",
				label: __("Activity Type"),
				fieldname: "activity_type",
				reqd: 1,
				options: "Activity Type",
			},
			{ fieldtype: "Link", label: __("Project"), fieldname: "project", options: "Project" },
			{ fieldtype: "Link", label: __("Task"), fieldname: "task", options: "Task" },
			{ fieldtype: "Float", label: __("Expected Hrs"), fieldname: "expected_hours" },
			{ fieldtype: "Datetime", label: __("From Time"), fieldname: "from_time" },
			{ fieldtype: "Float", label: __("Hours"), fieldname: "hours" },
			{ fieldtype: "Check", label: __("Is Billable"), fieldname: "is_billable" },
			{ fieldtype: "Section Break" },
			{ fieldtype: "HTML", fieldname: "timer_html" },
		],
	});

	if (row) {
		dialog.set_values({
			activity_type: row.activity_type,
			project: row.project,
			task: row.task,
			expected_hours: row.expected_hours,
			is_billable: row.is_billable,
		});
	} else {
		// Set default values for new time log
		const now = new Date();
		const pad = (value) => String(value).padStart(2, "0");
		const currentDate = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(
			now.getDate()
		)}`;
		const currentTime = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(
			now.getSeconds()
		)}`;

		const configuredActivityType =
			frappe?.boot?.projects_settings?.default_activity_type ??
			frappe?.boot?.project_hub?.default_activity_type ??
			frappe?.defaults?.get_user_default?.("activity_type") ??
			"Execution";

		dialog.set_values({
			project: frm.doc.parent_project,
			activity_type: configuredActivityType,
			from_time: currentDate + " " + currentTime,
			hours: 1, // Default to 1 hour
			is_billable: 0,
		});
	}

	dialog.get_field("timer_html").$wrapper.append(get_timer_html());

	function get_timer_html() {
		return `
			<div class="stopwatch">
				<span class="hours">00</span>
				<span class="colon">:</span>
				<span class="minutes">00</span>
				<span class="colon">:</span>
				<span class="seconds">00</span>
			</div>
			<div class="playpause text-center">
				<button class= "btn btn-primary btn-start"> ${__("Start")} </button>
				<button class= "btn btn-primary btn-complete"> ${__("Complete")} </button>
			</div>
		`;
	}

	$(document).on("keydown.timer_dialog", function (e) {
		if (e.key === "Escape" && dialog.$wrapper.is(":visible")) {
			dialog.hide();
		}
	});

	// Clean up escape key handler when dialog is hidden
	dialog.$wrapper.on("hidden.bs.modal", function () {
		$(document).off("keydown.timer_dialog");
	});

	dialog.show();
};
