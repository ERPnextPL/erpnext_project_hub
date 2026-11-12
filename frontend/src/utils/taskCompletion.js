import { getRealWindow, translate } from "./translation";

export async function promptForCompletionAssignee(taskName) {
	const win = getRealWindow();
	const frappe = win?.frappe;
	if (!frappe?.xcall) {
		throw new Error(translate("Task completion requires the Frappe interface."));
	}

	const assignees = await frappe.xcall(
		"erpnext_projekt_hub.api.project_hub.get_task_completion_assignees",
		{ task_name: taskName }
	);
	const currentUser = frappe.session?.user;
	if (
		assignees.length <= 1 ||
		assignees.some((assignee) => assignee.user === currentUser)
	) {
		return undefined;
	}

	if (!frappe.ui?.Dialog || !frappe.ui?.form?.make_control) {
		return promptWithHubDialog(assignees);
	}

	return new Promise((resolve) => {
		let settled = false;
		let dialog;
		const finish = (value) => {
			if (settled) return;
			settled = true;
			resolve(value);
			dialog?.hide();
		};

		dialog = new frappe.ui.Dialog({
			title: translate("Who completed this task?"),
			fields: [
				{
					fieldname: "completed_by",
					fieldtype: "Select",
					label: translate("Completed by"),
					options: assignees.map((assignee) => ({
						label: assignee.full_name
							? `${assignee.full_name} (${assignee.user})`
							: assignee.user,
						value: assignee.user,
					})),
					reqd: 1,
				},
			],
			primary_action_label: translate("Confirm"),
			primary_action(values) {
				if (values?.completed_by) finish(values.completed_by);
			},
			secondary_action_label: translate("Cancel"),
			secondary_action() {
				finish(null);
			},
		});
		dialog.onhide = () => {
			if (!settled) {
				settled = true;
				resolve(null);
			}
		};
		dialog.show();
	});
}

function promptWithHubDialog(assignees) {
	return new Promise((resolve) => {
		const previousFocus = document.activeElement;
		const overlay = document.createElement("div");
		overlay.className =
			"fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4";
		overlay.setAttribute("role", "presentation");

		const dialog = document.createElement("div");
		dialog.className = "w-full max-w-md rounded-xl bg-white p-5 shadow-xl dark:bg-gray-800";
		dialog.setAttribute("role", "dialog");
		dialog.setAttribute("aria-modal", "true");

		const title = document.createElement("h2");
		title.className = "mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100";
		title.textContent = translate("Who completed this task?");
		dialog.setAttribute("aria-label", title.textContent);

		const label = document.createElement("label");
		label.className = "mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300";
		label.textContent = translate("Completed by");

		const select = document.createElement("select");
		select.className =
			"w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100";
		assignees.forEach((assignee) => {
			const option = document.createElement("option");
			option.value = assignee.user;
			option.textContent = assignee.full_name
				? `${assignee.full_name} (${assignee.user})`
				: assignee.user;
			select.append(option);
		});
		label.append(select);

		const actions = document.createElement("div");
		actions.className = "mt-5 flex justify-end gap-2";

		const cancelButton = document.createElement("button");
		cancelButton.type = "button";
		cancelButton.className =
			"rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700";
		cancelButton.textContent = translate("Cancel");

		const confirmButton = document.createElement("button");
		confirmButton.type = "button";
		confirmButton.className =
			"rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700";
		confirmButton.textContent = translate("Confirm");

		actions.append(cancelButton, confirmButton);
		dialog.append(title, label, actions);
		overlay.append(dialog);

		let settled = false;
		const finish = (value) => {
			if (settled) return;
			settled = true;
			document.removeEventListener("keydown", handleKeydown);
			overlay.remove();
			if (previousFocus instanceof HTMLElement) previousFocus.focus();
			resolve(value);
		};
		const handleKeydown = (event) => {
			if (event.key === "Escape") finish(null);
			if (event.key === "Enter" && event.target === select) {
				event.preventDefault();
				finish(select.value);
			}
		};

		cancelButton.addEventListener("click", () => finish(null));
		confirmButton.addEventListener("click", () => finish(select.value));
		overlay.addEventListener("click", (event) => {
			if (event.target === overlay) finish(null);
		});
		document.addEventListener("keydown", handleKeydown);
		document.body.append(overlay);
		select.focus();
	});
}
