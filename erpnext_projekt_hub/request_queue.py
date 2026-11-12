"""Assignment queues and attachments shared by Customer Request and Change Request.

A request waiting for work is taken by one person. They are recorded in the
request's assignee field and get a ToDo assignment. The assignment closes once
the request leaves its queue; the field keeps who took it.
"""

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as add_assignment
from frappe.desk.form.assign_to import close_all_assignments
from frappe.desk.form.assign_to import remove as remove_assignment
from frappe.utils import get_fullname

# The workflow state in which each request type waits for an assignee.
QUEUE_STATES = {
	"Customer Request": "To Analyze",
	"Change Request": "Draft",
}
ASSIGNMENT_FIELDS = {
	"Customer Request": "analyst",
	"Change Request": "realization_assignee",
}


def get_request(doctype, name):
	if doctype not in QUEUE_STATES:
		frappe.throw(_("{0} is not a request.").format(doctype))
	return frappe.get_doc(doctype, name)


def is_in_queue(doc):
	return doc.workflow_state == QUEUE_STATES[doc.doctype]


def sync_request_assignment(doc):
	"""Keep the ToDo assignment in step with the assignee field and workflow state.

	Called from on_update, so it also covers a manager setting the assignee by hand.
	"""
	previous = doc.get_doc_before_save()
	queue_state = QUEUE_STATES[doc.doctype]
	was_in_queue = bool(previous and previous.workflow_state == queue_state)
	fieldname = ASSIGNMENT_FIELDS[doc.doctype]
	assignee = doc.get(fieldname)

	if not is_in_queue(doc):
		if was_in_queue:
			close_all_assignments(doc.doctype, doc.name, ignore_permissions=True)
		return

	previous_assignee = previous.get(fieldname) if previous else None
	if previous_assignee and previous_assignee != assignee:
		remove_assignment(doc.doctype, doc.name, previous_assignee)
	if assignee and (assignee != previous_assignee or not was_in_queue):
		assign_request(doc, assignee)


def assign_request(doc, user):
	add_assignment(
		{
			"doctype": doc.doctype,
			"name": doc.name,
			"assign_to": [user],
			"description": doc.subject,
		}
	)


def lock_request(doctype, name):
	"""Load a request with its row locked, so concurrent take/release see each other's writes."""
	request = get_request(doctype, name)
	request.check_permission("read")
	frappe.db.get_value(request.doctype, request.name, "name", for_update=True)
	request.reload()
	return request


@frappe.whitelist(methods=["POST"])
def take_for_analysis(doctype: str, name: str):
	"""Make the current user the analyst of a Customer Request waiting for analysis."""
	if doctype != "Customer Request":
		frappe.throw(_("Only Customer Requests can be taken for analysis."))
	return take_request(doctype, name)


@frappe.whitelist(methods=["POST"])
def take_for_realization(name: str):
	"""Make the current user the assignee of a Change Request waiting for realization."""
	return take_request("Change Request", name)


def take_request(doctype, name):
	# Two people clicking at once must not both get the same request.
	request = lock_request(doctype, name)

	if not is_in_queue(request):
		frappe.throw(_("Only requests waiting in their queue can be taken."))

	fieldname = ASSIGNMENT_FIELDS[doctype]
	assignee = request.get(fieldname)
	user = frappe.session.user
	if assignee and assignee != user:
		frappe.throw(_("{0} is already assigned to this request.").format(get_fullname(assignee)))

	if assignee != user:
		request.db_set(fieldname, user)
	assign_request(request, user)

	return {"name": request.name, "assignee": user}


@frappe.whitelist(methods=["POST"])
def release_analysis(doctype: str, name: str):
	"""Give a request the current user analyzes back to the analysis queue."""
	if doctype != "Customer Request":
		frappe.throw(_("Only Customer Requests can be released from analysis."))
	return release_request(doctype, name)


@frappe.whitelist(methods=["POST"])
def release_realization(name: str):
	"""Give a Change Request the current user owns back to the realization queue."""
	return release_request("Change Request", name)


def release_request(doctype, name):
	request = lock_request(doctype, name)

	if not is_in_queue(request):
		frappe.throw(_("Only requests waiting in their queue can be released."))

	user = frappe.session.user
	fieldname = ASSIGNMENT_FIELDS[doctype]
	assignee = request.get(fieldname)
	if assignee and assignee != user:
		frappe.throw(_("Only the person assigned to this request can release it."))

	if assignee:
		request.db_set(fieldname, None)
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
	file_doc.folder = frappe.db.get_value("File", {"is_attachments_folder": 1}) or file_doc.folder
	file_doc.save(ignore_permissions=True)
	file_doc.create_attachment_record()

	return {
		"name": file_doc.name,
		"file_name": file_doc.file_name,
		"file_url": file_doc.file_url,
		"is_private": file_doc.is_private,
	}


def get_attachments(doctype, names):
	"""Return {request name: [attachments]} for the given requests."""
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
