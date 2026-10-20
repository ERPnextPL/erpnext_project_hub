"""Analysis queue and attachments shared by Customer Request and Change Request.

A request waiting for analysis is taken by one person. They are recorded in the
request's `analyst` field, which is what the queue and the UI read, and get a
ToDo assignment so the request shows in their To Do list. The assignment closes
once the request leaves analysis; the field keeps who analyzed it. A request sent
back to analysis (Rejected -> To Analyze) returns to the queue without an analyst.

Anyone who can read a request may take it, release it and attach files to it:
analysis is usually done by developers whose role only reads Change Requests.
Picking someone else as analyst in the form is left to managers.
"""

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as add_assignment
from frappe.desk.form.assign_to import close_all_assignments
from frappe.desk.form.assign_to import remove as remove_assignment
from frappe.utils import get_fullname

# The workflow state in which each request type waits for analysis.
ANALYSIS_STATES = {
	"Customer Request": "To Analyze",
	"Change Request": "Draft",
}
# Roles that may set or change the analyst in the form (assign someone else).
ANALYST_MANAGER_ROLES = ("Projects Manager", "Project Manager", "System Manager")


def get_request(doctype, name):
	if doctype not in ANALYSIS_STATES:
		frappe.throw(_("{0} is not a request.").format(doctype))
	return frappe.get_doc(doctype, name)


def is_in_analysis(doc):
	return doc.workflow_state == ANALYSIS_STATES[doc.doctype]


def validate_analyst(doc):
	"""Called from validate: who may change the analyst, and the queue on re-entry.

	Take/Release write the field with db_set and never reach validate, so a change
	seen here comes from the form or the REST API.
	"""
	previous = doc.get_doc_before_save()
	# has_value_changed is always True on a new document, so compare explicitly.
	if (previous.analyst if previous else None) != (doc.analyst or None):
		if doc.analyst and not frappe.db.get_value("User", doc.analyst, "enabled"):
			frappe.throw(_("User {0} is disabled.").format(doc.analyst))
		frappe.only_for(ANALYST_MANAGER_ROLES)

	analysis_state = ANALYSIS_STATES[doc.doctype]
	if previous and previous.workflow_state != analysis_state and is_in_analysis(doc):
		# A new round of analysis starts unassigned, so a former analyst who left
		# or is away does not keep the request out of the queue.
		doc.analyst = None


def sync_analysis_assignment(doc):
	"""Keep the ToDo assignment in step with the analyst field and the workflow state.

	Called from on_update, so it also covers a manager setting the analyst by hand.
	"""
	previous = doc.get_doc_before_save()
	analysis_state = ANALYSIS_STATES[doc.doctype]
	was_in_analysis = bool(previous and previous.workflow_state == analysis_state)

	if not is_in_analysis(doc):
		if was_in_analysis:
			close_all_assignments(doc.doctype, doc.name, ignore_permissions=True)
		return

	previous_analyst = previous.analyst if previous else None
	# Only an assignment of the current analysis round is still open.
	if was_in_analysis and previous_analyst and previous_analyst != doc.analyst:
		remove_assignment(doc.doctype, doc.name, previous_analyst)
	if doc.analyst and (doc.analyst != previous_analyst or not was_in_analysis):
		assign_analyst(doc, doc.analyst)


def assign_analyst(doc, user):
	add_assignment(
		{
			"doctype": doc.doctype,
			"name": doc.name,
			"assign_to": [user],
			"description": doc.subject,
		}
	)


def lock_request(doctype, name):
	"""Load a request with its row locked, so concurrent take/release see each other's writes.

	The reload itself must be the locking read (SELECT ... FOR UPDATE): a plain read
	after taking the lock would still see the REPEATABLE READ snapshot from before the
	lock wait, so a second user would miss the first one's claim.
	"""
	request = get_request(doctype, name)
	request.check_permission("read")
	request.flags.for_update = True
	request.reload()
	return request


@frappe.whitelist(methods=["POST"])
def take_for_analysis(doctype: str, name: str):
	"""Make the current user the analyst of a request waiting for analysis."""
	# Two people clicking "Take for analysis" at once must not both get it.
	request = lock_request(doctype, name)

	if not is_in_analysis(request):
		frappe.throw(_("Only requests waiting for analysis can be taken."))

	user = frappe.session.user
	if request.analyst and request.analyst != user:
		frappe.throw(_("{0} is already analyzing this request.").format(get_fullname(request.analyst)))

	if request.analyst != user:
		request.db_set("analyst", user)
	assign_analyst(request, user)

	return {"name": request.name, "analyst": user}


@frappe.whitelist(methods=["POST"])
def release_analysis(doctype: str, name: str):
	"""Give a request the current user analyzes back to the analysis queue."""
	request = lock_request(doctype, name)

	# Once analysis is over the field records who analyzed the request.
	if not is_in_analysis(request):
		frappe.throw(_("Only requests waiting for analysis can be released."))

	user = frappe.session.user
	if request.analyst and request.analyst != user:
		frappe.throw(_("Only the person analyzing the request can release it."))

	if request.analyst:
		request.db_set("analyst", None)
	remove_assignment(request.doctype, request.name, user)

	return {"name": request.name}


@frappe.whitelist(methods=["POST"])
def attach_file(doctype: str, name: str, file_name: str):
	"""Attach a file the current user just uploaded to a request they can open.

	Frappe attaches files only for users who may edit the document, but anyone who
	can read a request may add attachments to it. The file is uploaded unattached
	first (File creation is open to every user), then linked here.
	"""
	request = get_request(doctype, name)
	request.check_permission("read")

	file_doc = frappe.get_doc("File", file_name)
	if file_doc.is_folder or file_doc.owner != frappe.session.user or file_doc.attached_to_doctype:
		frappe.throw(_("Only a file you have just uploaded can be attached."), frappe.PermissionError)

	file_doc.attached_to_doctype = request.doctype
	file_doc.attached_to_name = request.name
	# File.before_insert checked the limit while the file was not attached yet.
	file_doc.validate_attachment_limit()
	file_doc.folder = frappe.db.get_value("File", {"is_attachments_folder": 1}) or file_doc.folder
	# Without ignore_permissions File.validate demands write permission on the request,
	# which is what this endpoint deliberately does not require (read is checked above).
	file_doc.save(ignore_permissions=True)
	file_doc.create_attachment_record()

	return {
		"name": file_doc.name,
		"file_name": file_doc.file_name,
		"file_url": file_doc.file_url,
		"is_private": file_doc.is_private,
	}


def get_attachments(doctype, names):
	"""Return {request name: [attachments]} for the given requests.

	Reads File without permission checks, so `names` must come from a permission-aware
	query of requests the user may read (get_project_requests uses frappe.get_list).
	"""
	if not names:
		return {}

	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": doctype, "attached_to_name": ["in", names], "is_folder": 0},
		fields=["name", "file_name", "file_url", "is_private", "attached_to_name", "creation"],
		order_by="creation desc",
		ignore_permissions=True,
	)
	attachments = {}
	for file in files:
		attachments.setdefault(file.pop("attached_to_name"), []).append(file)
	return attachments
