"""Approval of Timesheets: an employee sends hours, an approver approves or rejects them.

The approval stage lives in ``workflow_state`` (workflow "Timesheet Approval"):

	Draft --Send for Approval--> Pending Approval --Approve--> Approved --Cancel--> Cancelled
	                                     |  ^
	                                Reject  Resubmit
	                                     v  |
	                                   Rejected

The standard ``status`` field keeps tracking billing (Submitted, Billed, Payslip, ...).
Approving submits the timesheet, so only approved hours reach costs, invoices and payroll.

Frappe enforces the workflow's "allow edit" roles in the browser only, and lets anyone with
the Submit permission submit around the workflow. The document hooks below close both gaps
on the server: a timesheet waiting for approval stays locked for its author, and it is
submitted or cancelled only through the workflow.
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import (
	cstr,
	escape_html,
	format_date,
	format_datetime,
	get_url,
	get_url_to_form,
	now_datetime,
)

DOCTYPE = "Timesheet"
WORKFLOW_NAME = "Timesheet Approval"
STATE_FIELD = "workflow_state"

DRAFT = "Draft"
PENDING = "Pending Approval"
APPROVED = "Approved"
REJECTED = "Rejected"
CANCELLED = "Cancelled"

SEND_FOR_APPROVAL = "Send for Approval"
APPROVE = "Approve"
REJECT = "Reject"
RESUBMIT = "Resubmit"
CANCEL = "Cancel"

TIMESHEET_MANAGER = "Timesheet Manager"
APPROVER_ROLES = (TIMESHEET_MANAGER, "Projects Manager")
CANCEL_ROLES = (TIMESHEET_MANAGER,)
# Roles that log their own hours. "Employee Self Service" comes with HRMS and may be missing.
EMPLOYEE_ROLES = ("Employee", "Employee Self Service", "Projects User")
# Submitting is the approval itself, so these roles lose Submit on Timesheet.
ROLES_WITHOUT_SUBMIT = ("Employee Self Service", "Projects User", "HR User")

APPROVER_PERMISSIONS = {
	TIMESHEET_MANAGER: (
		"read",
		"write",
		"create",
		"delete",
		"submit",
		"cancel",
		"amend",
		"report",
		"export",
		"print",
		"email",
		"share",
	),
	"Projects Manager": ("read", "write", "create", "submit", "report", "export", "print", "email", "share"),
}
# Saving a timesheet recalculates its tasks and projects, so ERPNext requires the person
# approving or rejecting it to be allowed to pick them; approvers also need to open them.
# Standard ERPNext gives Projects Manager no Task access and Timesheet Manager is new.
RELATED_READ_ACCESS = {
	"Task": APPROVER_ROLES,
	"Project": APPROVER_ROLES,
}

# Workflow State records are shared by every workflow. These three colours are part of the
# process (list and form indicators), the others are only created when missing.
STATE_STYLES = {PENDING: "Warning", APPROVED: "Success", REJECTED: "Danger"}
DEFAULT_STATE_STYLES = {DRAFT: "", CANCELLED: "Inverse"}

# Approver queue on the Projects workspace. Filters use the 4-item form, see
# setup_customer_change_requests.ANALYSIS_QUEUE_FILTERS.
TO_APPROVE_FILTERS = [[DOCTYPE, STATE_FIELD, "=", PENDING]]
TO_APPROVE_SHORTCUT = ("Timesheets to Approve", DOCTYPE, "Orange", TO_APPROVE_FILTERS, "{} to approve")

CUSTOM_FIELDS = {
	DOCTYPE: [
		{
			"fieldname": "approval_section",
			"fieldtype": "Section Break",
			"label": "Approval",
			"insert_after": "end_date",
		},
		{
			"fieldname": STATE_FIELD,
			"fieldtype": "Link",
			"options": "Workflow State",
			"label": "Approval Status",
			"insert_after": "approval_section",
			"read_only": 1,
			"allow_on_submit": 1,
			"no_copy": 1,
			"in_standard_filter": 1,
		},
		{
			"fieldname": "approval_requested_on",
			"fieldtype": "Datetime",
			"label": "Sent for Approval On",
			"insert_after": STATE_FIELD,
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "approval_column_break",
			"fieldtype": "Column Break",
			"insert_after": "approval_requested_on",
		},
		{
			"fieldname": "reviewed_by",
			"fieldtype": "Link",
			"options": "User",
			"label": "Reviewed By",
			"insert_after": "approval_column_break",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "reviewed_on",
			"fieldtype": "Datetime",
			"label": "Reviewed On",
			"insert_after": "reviewed_by",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "rejection_reason",
			"fieldtype": "Small Text",
			"label": "Rejection Reason",
			"description": "Required when rejecting. The employee sees it and corrects the hours.",
			"insert_after": "reviewed_on",
			"read_only": 1,
			"no_copy": 1,
			"depends_on": "eval:doc.rejection_reason",
		},
	]
}


# Setup
# -----


def setup():
	"""Create (or re-sync) everything the approval process needs. Safe to run repeatedly."""
	ensure_roles()
	ensure_workflow_states_and_actions()
	create_custom_fields(CUSTOM_FIELDS, update=True)
	ensure_workflow()
	ensure_permissions()
	backfill_workflow_state()
	ensure_workspace_shortcut()


def ensure_roles():
	if not frappe.db.exists("Role", TIMESHEET_MANAGER):
		frappe.get_doc({"doctype": "Role", "role_name": TIMESHEET_MANAGER, "desk_access": 1}).insert(
			ignore_permissions=True
		)


def ensure_workflow_states_and_actions():
	for state, style in {**DEFAULT_STATE_STYLES, **STATE_STYLES}.items():
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
			).insert(ignore_permissions=True)
		elif state in STATE_STYLES and frappe.db.get_value("Workflow State", state, "style") != style:
			frappe.db.set_value("Workflow State", state, "style", style)

	for action in (SEND_FOR_APPROVAL, APPROVE, REJECT, RESUBMIT, CANCEL):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
				ignore_permissions=True
			)


def ensure_workflow():
	employee_roles = _existing_roles(EMPLOYEE_ROLES)
	approver_roles = _existing_roles(APPROVER_ROLES)
	cancel_roles = _existing_roles(CANCEL_ROLES)
	authors = _unique(employee_roles + approver_roles)

	# One row per role that may edit the document in that state. Pending Approval is
	# "optional" so that drafts do not create Workflow Actions for every employee;
	# the approvers get theirs when a timesheet starts waiting for them.
	states = [
		(DRAFT, "0", authors, {}),
		(PENDING, "0", approver_roles, {"is_optional_state": 1}),
		(REJECTED, "0", authors, {"is_optional_state": 1}),
		# The list and form show the billing status (Billed, Payslip, ...) of approved timesheets.
		(APPROVED, "1", cancel_roles, {"avoid_status_override": 1}),
		(CANCELLED, "2", cancel_roles, {"is_optional_state": 1}),
	]
	transitions = [
		(DRAFT, SEND_FOR_APPROVAL, PENDING, authors),
		(PENDING, APPROVE, APPROVED, approver_roles),
		(PENDING, REJECT, REJECTED, approver_roles),
		(REJECTED, RESUBMIT, PENDING, authors),
		(APPROVED, CANCEL, CANCELLED, cancel_roles),
	]

	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		workflow = frappe.get_doc("Workflow", WORKFLOW_NAME)
	else:
		workflow = frappe.new_doc("Workflow")
		workflow.workflow_name = WORKFLOW_NAME

	workflow.document_type = DOCTYPE
	workflow.workflow_state_field = STATE_FIELD
	workflow.is_active = 1
	workflow.override_status = 0
	# The Hub sends its own e-mails (see notify); Frappe's would offer Reject without a reason.
	workflow.send_email_alert = 0
	workflow.set(
		"states",
		[
			{"state": state, "doc_status": doc_status, "allow_edit": role, **extra}
			for state, doc_status, roles, extra in states
			for role in roles
		],
	)
	workflow.set(
		"transitions",
		[
			{
				"state": state,
				"action": action,
				"next_state": next_state,
				"allowed": role,
				"allow_self_approval": 1,
			}
			for state, action, next_state, roles in transitions
			for role in roles
		],
	)
	workflow.save(ignore_permissions=True)


def ensure_permissions():
	"""Submit comes only from the Approve transition; approvers get the rights they need for it."""
	from frappe.permissions import setup_custom_perms

	setup_custom_perms(DOCTYPE)

	for name in frappe.get_all(
		"Custom DocPerm",
		filters={"parent": DOCTYPE, "role": ["in", ROLES_WITHOUT_SUBMIT], "submit": 1},
		pluck="name",
	):
		frappe.db.set_value("Custom DocPerm", name, "submit", 0)

	for role, rights in APPROVER_PERMISSIONS.items():
		_grant(DOCTYPE, role, rights)

	for doctype, roles in RELATED_READ_ACCESS.items():
		for role in roles:
			_grant(doctype, role, ("read", "select"))

	for doctype in (DOCTYPE, *RELATED_READ_ACCESS):
		frappe.clear_cache(doctype=doctype)


def _grant(doctype, role, rights):
	"""Add rights to the role's level-0 rule of the doctype, keeping the rights it has."""
	from frappe.permissions import setup_custom_perms

	if not frappe.db.exists("Role", role):
		return
	setup_custom_perms(doctype)

	name = frappe.db.get_value(
		"Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0}
	)
	if name:
		perm = frappe.get_doc("Custom DocPerm", name)
		if all(perm.get(right) for right in rights):
			return
	else:
		perm = frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": doctype,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": role,
				"permlevel": 0,
			}
		)
	for right in rights:
		perm.set(right, 1)
	perm.save(ignore_permissions=True)


def backfill_workflow_state():
	"""Existing timesheets: Draft stays Draft, submitted ones count as Approved, cancelled as Cancelled."""
	Timesheet = frappe.qb.DocType(DOCTYPE)
	state_field = Timesheet[STATE_FIELD]
	for docstatus, state in ((0, DRAFT), (1, APPROVED), (2, CANCELLED)):
		(
			frappe.qb.update(Timesheet)
			.set(state_field, state)
			.where(Timesheet.docstatus == docstatus)
			.where(state_field.isnull() | (state_field == ""))
		).run()


def ensure_workspace_shortcut():
	from erpnext_projekt_hub.patches.post_model_sync.setup_customer_change_requests import (
		WORKSPACE_NAME,
		ensure_shortcut_in_content,
		ensure_workspace_filtered_shortcut,
	)

	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = ensure_workspace_filtered_shortcut(workspace, *TO_APPROVE_SHORTCUT)
	content, content_changed = ensure_shortcut_in_content(workspace.content, TO_APPROVE_SHORTCUT[0])
	if content_changed:
		workspace.content = content
		changed = True

	if changed:
		workspace.flags.ignore_links = True
		workspace.save(ignore_permissions=True)


# Document hooks
# --------------


def is_enabled() -> bool:
	"""True while the Hub's approval workflow is the active workflow for Timesheet."""
	from frappe.model.workflow import get_workflow_name

	return get_workflow_name(DOCTYPE) == WORKFLOW_NAME


def validate(doc, method=None):
	if not is_enabled() or doc.flags.ignore_timesheet_approval:
		return

	before = doc.get_doc_before_save()
	old_state = before.get(STATE_FIELD) if before else None
	new_state = doc.get(STATE_FIELD)

	if old_state == new_state:
		if new_state == PENDING and not can_review():
			frappe.throw(
				_(
					"This timesheet is waiting for approval, so its hours cannot be changed. "
					"If something needs correcting, ask the approver to reject it."
				),
				title=_("Waiting for approval"),
			)
		return

	if new_state == PENDING:
		doc.approval_requested_on = now_datetime()
		# The decision on the previous version no longer applies; the timeline keeps it.
		doc.reviewed_by = None
		doc.reviewed_on = None
		doc.rejection_reason = None
	elif new_state in (APPROVED, REJECTED):
		if new_state == REJECTED and not cstr(doc.rejection_reason).strip():
			frappe.throw(
				_("Please enter the reason for rejection, so the employee knows what to correct."),
				title=_("Rejection reason required"),
			)
		doc.reviewed_by = frappe.session.user
		doc.reviewed_on = now_datetime()


def before_submit(doc, method=None):
	if not is_enabled() or doc.flags.ignore_timesheet_approval:
		return

	# The Approve transition sets the state before submitting; a plain Submit does not.
	if doc.get(STATE_FIELD) != APPROVED:
		frappe.throw(
			_(
				"A timesheet is submitted by approving it. Send it for approval; "
				"a Timesheet Manager or Projects Manager then approves it."
			),
			title=_("Approval required"),
		)


def before_cancel(doc, method=None):
	if not is_enabled() or doc.flags.ignore_timesheet_approval:
		return

	if not _has_any_role(CANCEL_ROLES):
		frappe.throw(
			_("Only a Timesheet Manager can cancel an approved timesheet."),
			frappe.PermissionError,
			title=_("Not allowed"),
		)
	# Frappe skips workflow validation on cancel, so a plain Cancel would keep "Approved".
	doc.set(STATE_FIELD, CANCELLED)


def on_change(doc, method=None):
	if not is_enabled() or doc.flags.ignore_timesheet_approval:
		return

	before = doc.get_doc_before_save()
	if not before or before.get(STATE_FIELD) == doc.get(STATE_FIELD):
		return

	state = doc.get(STATE_FIELD)
	if state == REJECTED:
		doc.add_comment("Comment", _("Rejection reason: {0}").format(escape_html(doc.rejection_reason)))

	if state in (PENDING, APPROVED, REJECTED, CANCELLED):
		notify(doc, state)


def can_review(user: str | None = None) -> bool:
	"""True when the user may approve and reject timesheets."""
	return _has_any_role(APPROVER_ROLES, user)


def _has_any_role(roles, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(set(frappe.get_roles(user)) & set(roles))


# Rejection with a reason
# -----------------------


@frappe.whitelist(methods=["POST"])
def reject_timesheet(timesheet: str, reason: str):
	"""Reject a timesheet waiting for approval and store why.

	The standard workflow action reloads the document from the database before it
	applies the transition, so the reason has to be stored first. If the user may not
	reject, the transition throws and the request rolls back the reason with it.
	"""
	from frappe.model.workflow import apply_workflow, get_transitions

	reason = cstr(reason).strip()
	if not reason:
		frappe.throw(
			_("Please enter the reason for rejection, so the employee knows what to correct."),
			title=_("Rejection reason required"),
		)

	doc = frappe.get_doc(DOCTYPE, timesheet)
	doc.check_permission("read")
	if doc.get(STATE_FIELD) != PENDING:
		frappe.throw(_("Only a timesheet waiting for approval can be rejected."))
	if not any(transition.action == REJECT for transition in get_transitions(doc)):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	frappe.db.set_value(DOCTYPE, doc.name, "rejection_reason", reason, update_modified=False)
	doc = apply_workflow(frappe.get_doc(DOCTYPE, doc.name), REJECT)
	return {"workflow_state": doc.get(STATE_FIELD)}


# Notifications
# -------------


def notify(doc, state):
	"""Desk notification and e-mail for the people who act next. Never blocks the transition.

	The desk notification (bell) always goes out; the e-mail only when the site has an
	outgoing e-mail account, so a missing account neither fails nor shows an error.
	"""
	# A failure below must not leave its message on screen after a successful transition.
	saved_messages = frappe.get_message_log()
	try:
		if state == PENDING:
			recipients = get_approvers(doc)
		else:
			recipients = [get_employee_user(doc)]

		actor = frappe.session.user
		recipients = [user for user in _unique(recipients) if user and user not in (actor, "Guest")]
		if not recipients:
			return

		send_email = _has_outgoing_email_account()
		for lang, users in _group_by_language(recipients).items():
			with _language(lang):
				subject, message = _render_notification(doc, state)
				_create_desk_notification(doc, users, subject, message)
				if send_email:
					frappe.sendmail(
						recipients=users,
						subject=subject,
						message=message,
						reference_doctype=DOCTYPE,
						reference_name=doc.name,
					)
	except Exception:
		frappe.log_error(title=f"Timesheet approval notification failed for {doc.name}")
	finally:
		frappe.local.message_log = saved_messages


def _has_outgoing_email_account() -> bool:
	from frappe.email.doctype.email_account.email_account import EmailAccount

	return bool(EmailAccount.find_outgoing(match_by_doctype=DOCTYPE))


def get_employee_user(doc) -> str | None:
	"""The user whose hours the timesheet holds."""
	if doc.employee:
		user = frappe.db.get_value("Employee", doc.employee, "user_id")
		if user:
			return user
	return doc.get("user") or doc.owner


def get_approvers(doc) -> list[str]:
	"""Who should approve: the project manager(s), else the employee's supervisor,
	else every Timesheet Manager, else every Projects Manager.

	Only enabled users who may actually approve are returned, never the employee.
	"""
	employee_user = get_employee_user(doc)

	candidates = []
	if frappe.db.has_column("Project", "project_manager"):
		projects = {row.project for row in doc.time_logs if row.project}
		if doc.parent_project:
			projects.add(doc.parent_project)
		if projects:
			candidates += frappe.get_all(
				"Project", filters={"name": ["in", sorted(projects)]}, pluck="project_manager"
			)

	if doc.employee:
		supervisor = frappe.db.get_value("Employee", doc.employee, "reports_to")
		if supervisor:
			candidates.append(frappe.db.get_value("Employee", supervisor, "user_id"))

	approvers = [
		user
		for user in _unique(candidates)
		if user and user != employee_user and _is_active_user(user) and can_review(user)
	]
	if approvers:
		return approvers

	for role in APPROVER_ROLES:
		approvers = [user for user in _users_with_role(role) if user != employee_user]
		if approvers:
			return approvers
	return []


def _render_notification(doc, state):
	employee = escape_html(doc.employee_name or get_employee_user(doc) or "")
	reviewer = escape_html(frappe.utils.get_fullname(frappe.session.user))
	name = escape_html(doc.name)

	if state == PENDING:
		subject = _("Timesheet {0} of {1} is waiting for your approval").format(name, employee)
		intro = _("{0} sent hours for approval. Check them, then approve or reject the timesheet.").format(
			employee
		)
	elif state == APPROVED:
		subject = _("Your timesheet {0} has been approved").format(name)
		intro = _(
			"{0} approved your hours. They now count towards project costs, invoices and payroll."
		).format(reviewer)
	elif state == REJECTED:
		subject = _("Your timesheet {0} has been rejected").format(name)
		intro = _("{0} rejected your hours. Correct them and send the timesheet for approval again.").format(
			reviewer
		)
	else:
		subject = _("Your approved timesheet {0} has been cancelled").format(name)
		intro = _(
			"{0} cancelled your approved timesheet. Its hours no longer count towards project costs, invoices and payroll."
		).format(reviewer)

	period = format_date(doc.start_date)
	if doc.end_date and doc.end_date != doc.start_date:
		period = f"{period} - {format_date(doc.end_date)}"

	rows = [
		(_("Employee"), employee),
		(_("Period"), period),
		(_("Hours"), frappe.format_value(doc.total_hours, {"fieldtype": "Float"})),
	]
	if state == PENDING and doc.get("approval_requested_on"):
		rows.append((_("Sent for Approval On"), format_datetime(doc.approval_requested_on)))
	if state == REJECTED:
		rows.append((_("Rejection Reason"), escape_html(doc.rejection_reason).replace("\n", "<br>")))

	table = "".join(
		f'<tr><td style="padding:4px 16px 4px 0;color:#6b7280;">{label}</td>'
		f'<td style="padding:4px 0;"><strong>{value}</strong></td></tr>'
		for label, value in rows
	)
	links = [f'<a href="{get_url_to_form(DOCTYPE, doc.name)}">{_("Open the timesheet")}</a>']
	if state != PENDING:
		links.append(
			f'<a href="{get_url("/project-hub/my-time-logs")}">{_("See your hours in Projekt HUB")}</a>'
		)

	message = (
		f"<p>{intro}</p>"
		f'<table style="border-collapse:collapse;margin:12px 0;">{table}</table>'
		f"<p>{' &nbsp;·&nbsp; '.join(links)}</p>"
	)
	return subject, message


def _create_desk_notification(doc, users, subject, message):
	from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

	enqueue_create_notification(
		users,
		{
			# "Alert" logs never e-mail, the e-mail above is sent separately.
			"type": "Alert",
			"document_type": DOCTYPE,
			"document_name": doc.name,
			"subject": subject,
			"email_content": message,
			"from_user": frappe.session.user,
		},
	)


def _group_by_language(users):
	default = frappe.db.get_single_value("System Settings", "language") or "en"
	groups = {}
	for user in users:
		lang = frappe.db.get_value("User", user, "language") or default
		groups.setdefault(lang, []).append(user)
	return groups


def _language(lang):
	from frappe.translate import print_language

	return print_language(lang)


def _users_with_role(role) -> list[str]:
	users = frappe.get_all(
		"Has Role", filters={"role": role, "parenttype": "User"}, pluck="parent", distinct=True
	)
	if not users:
		return []
	return frappe.get_all(
		"User",
		filters=[
			["name", "in", users],
			["name", "not in", ("Administrator", "Guest")],
			["enabled", "=", 1],
			["user_type", "=", "System User"],
		],
		pluck="name",
		order_by="name",
	)


def _is_active_user(user) -> bool:
	return user not in ("Administrator", "Guest") and bool(frappe.db.get_value("User", user, "enabled"))


def _existing_roles(roles) -> list[str]:
	return [role for role in roles if frappe.db.exists("Role", role)]


def _unique(values):
	return list(dict.fromkeys(values))
