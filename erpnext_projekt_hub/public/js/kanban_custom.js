(function () {
	frappe.provide("erpnext_projekt_hub.kanban");

	const hasRenderedKanban = () => {
		return frappe.views && frappe.views.KanbanBoardCard;
	};

	const attachKanbanExtensions = () => {
		if (!hasRenderedKanban()) {
			return;
		}

		const originalKanbanCard = frappe.views.KanbanBoardCard.__erpnext_projekt_hub_original
			? frappe.views.KanbanBoardCard.__erpnext_projekt_hub_original
			: frappe.views.KanbanBoardCard;

		if (frappe.views.KanbanBoardCard.__erpnext_projekt_hub_patched) {
			return;
		}

		const patchedKanbanCard = function (card, wrapper) {
			const kanbanInstance = originalKanbanCard(card, wrapper);
			enhanceKanbanCard(card, kanbanInstance);
			return kanbanInstance;
		};

		patchedKanbanCard.__erpnext_projekt_hub_original = originalKanbanCard;
		patchedKanbanCard.__erpnext_projekt_hub_patched = true;

		frappe.views.KanbanBoardCard = patchedKanbanCard;

		if (frappe.views.KanbanBoard) {
			frappe.views.KanbanBoard.show_task_preview = function (taskName) {
				frappe.call({
					method: "frappe.client.get",
					args: {
						doctype: "Task",
						name: taskName,
					},
					callback: function (r) {
						if (r?.message) {
							showTaskPreviewDialog(r.message);
						}
					},
				});
			};
		}
	};

	const enhanceKanbanCard = function (card, kanbanInstance) {
		if (!card || card.doctype !== "Task" || !kanbanInstance || !kanbanInstance.$card) {
			return;
		}

		const $wrapper = kanbanInstance.$card;
		const $content = $wrapper.find(".kanban-card.content");
		const $meta = $wrapper.find(".kanban-card-meta");

		$wrapper.addClass("erpnext-projekt-hub-kanban-card");

		const $customMeta = getMetaContainer($meta);
		fillMetaDetails(card, $customMeta);

		bindPreviewHandler(card, $content, $meta);
	};

	const getMetaContainer = ($meta) => {
		if (!$meta.length) {
			return null;
		}

		let $container = $meta.find(".project-hub-kanban-meta");
		if (!$container.length) {
			$container = $("<div class='project-hub-kanban-meta'></div>");
			$meta.prepend($container);
		} else {
			$container.empty();
		}

		return $container;
	};

	const fillMetaDetails = (card, $container) => {
		if (!$container) {
			return;
		}

		if (card.exp_end_date) {
			const dueDate = frappe.utils.escape_html(card.exp_end_date);
			$container.append(
				"<div class='kanban-meta-item'><span class='small'><svg class='icon icon-sm' style='width: 12px; height: 12px;'><use href='#icon-calendar'></use></svg> " +
					dueDate +
					"</span></div>"
			);
		}

		if (card.priority) {
			const priorityValue = frappe.utils.escape_html(card.priority);
			const priorityClass = `badge-${card.priority
				.toString()
				.toLowerCase()
				.replace(/[^a-z0-9]+/g, "-")}`;
			const badgeClasses = `priority-badge text-nowrap ${priorityClass}`;
			$container.append(
				`<div class='kanban-meta-item'><span class='${badgeClasses}'>${priorityValue}</span></div>`
			);
		}

		const subtaskCount = Number(card.subtask_count || card.subtasks || 0);
		if (subtaskCount > 0) {
			const subtaskLabel = subtaskCount === 1 ? __("Subtask") : __("Subtasks");
			$container.append(
				"<div class='kanban-meta-item'><span class='text-muted small'><svg class='icon icon-sm' style='width: 12px; height: 12px;'><use href='#icon-list'></use></svg> " +
					`${subtaskCount} ${subtaskLabel}` +
					"</span></div>"
			);
		}

		const assignees = parseAssignees(card._assign);
		if (assignees.length) {
			const $avatarGroup = $(
				"<div class='kanban-meta-item'><div class='project-hub-avatar-group'></div></div>"
			);
			const $list = $avatarGroup.find(".project-hub-avatar-group");
			assignees.slice(0, 6).forEach((assignee) => {
				const safeAssignee = frappe.utils.escape_html(assignee || "");
				const initials = safeAssignee.toString().charAt(0).toUpperCase();
				const $avatar = $(
					`<span class='project-hub-avatar' title='${safeAssignee}'>${initials}</span>`
				);
				$list.append($avatar);
			});

			$container.append($avatarGroup);
		}
	};

	const bindPreviewHandler = (card, $content, $meta) => {
		if (!$content.length) {
			return;
		}

		$content.off("click.erpnext-projekt-hub");
		$content.on("click.erpnext-projekt-hub", function (event) {
			if (card._disable_click) {
				return;
			}

			if ($(event.target).closest(".kanban-card-meta").length) {
				return;
			}

			event.preventDefault();
			event.stopPropagation();

			frappe.views.KanbanBoard.show_task_preview(card.name);
		});
	};

	const parseAssignees = (value) => {
		if (!value) {
			return [];
		}

		if (Array.isArray(value)) {
			return value;
		}

		if (typeof value === "string") {
			try {
				return JSON.parse(value);
			} catch (error) {
				return [value];
			}
		}

		return [];
	};

	const showTaskPreviewDialog = (task) => {
		if (!task) {
			return;
		}

		const dialog = new frappe.ui.Dialog({
			title: `${__("Task Preview")}: ${task.name}`,
			fields: [
				{ fieldtype: "Section Break", label: __("Task Details") },
				{ fieldname: "subject", fieldtype: "Data", label: __("Subject"), read_only: 1 },
				{
					fieldname: "description",
					fieldtype: "Text Editor",
					label: __("Description"),
					read_only: 1,
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "status",
					fieldtype: "Link",
					options: "Task Status",
					label: __("Status"),
					read_only: 1,
				},
				{
					fieldname: "priority",
					fieldtype: "Link",
					options: "Task Priority",
					label: __("Priority"),
					read_only: 1,
				},
				{ fieldtype: "Section Break", label: __("Dates & Assignment") },
				{
					fieldname: "exp_end_date",
					fieldtype: "Date",
					label: __("End Date"),
					read_only: 1,
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "_assign",
					fieldtype: "MultiSelectList",
					options: "User",
					label: __("Assignees"),
					read_only: 1,
				},
				{ fieldtype: "Section Break", label: __("Project Details") },
				{
					fieldname: "project",
					fieldtype: "Link",
					options: "Project",
					label: __("Project"),
					read_only: 1,
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "progress",
					fieldtype: "Percent",
					label: __("Progress"),
					read_only: 1,
				},
			],
			size: "large",
			primary_action: function () {
				dialog.hide();
				frappe.set_route("Form", "Task", task.name);
			},
			primary_action_label: __("Open Full Form"),
		});

		dialog.set_value("subject", task.subject);
		dialog.set_value("description", task.description);
		dialog.set_value("status", task.status);
		dialog.set_value("priority", task.priority);
		dialog.set_value("exp_end_date", task.exp_end_date);
		dialog.set_value("project", task.project);
		dialog.set_value("progress", task.progress || 0);

		const assignees = parseAssignees(task._assign);
		if (assignees.length) {
			dialog.set_value("_assign", assignees);
		}

		dialog.add_custom_action(__("Edit Task"), function () {
			dialog.hide();
			frappe.set_route("Form", "Task", task.name);
		});

		dialog.show();
	};

	const ensureKanbanHook = () => {
		if (hasRenderedKanban()) {
			attachKanbanExtensions();
		} else {
			setTimeout(ensureKanbanHook, 200);
		}
	};

	frappe.dom_ready(function () {
		ensureKanbanHook();
	});
})();
