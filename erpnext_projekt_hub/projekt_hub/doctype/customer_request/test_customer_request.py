import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext_projekt_hub.api.project_hub import get_project_requests


def get_or_create_test_company():
	company_name = "_Test Project Hub Company"
	if frappe.db.exists("Company", company_name):
		return company_name

	if not frappe.db.exists("Warehouse Type", "Transit"):
		frappe.get_doc(
			{
				"doctype": "Warehouse Type",
				"name": "Transit",
			}
		).insert(ignore_permissions=True)

	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": company_name,
			"abbr": "TPH",
			"default_currency": "PLN",
			"country": "Poland",
		}
	).insert(ignore_permissions=True)
	return company_name


def get_or_create_customer():
	customer_name = "_Test Project Hub Customer"
	if frappe.db.exists("Customer", customer_name):
		return customer_name

	if not frappe.db.exists("Customer Group", "_Test Customer Group"):
		frappe.get_doc(
			{
				"doctype": "Customer Group",
				"customer_group_name": "_Test Customer Group",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Territory", "_Test Territory"):
		frappe.get_doc(
			{
				"doctype": "Territory",
				"territory_name": "_Test Territory",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)

	frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": customer_name,
			"customer_type": "Company",
			"customer_group": "_Test Customer Group",
			"territory": "_Test Territory",
		}
	).insert(ignore_permissions=True)
	return customer_name


def create_project(customer):
	project = frappe.get_doc(
		{
			"doctype": "Project",
			"project_name": frappe.generate_hash("request-test-", 8),
			"company": get_or_create_test_company(),
			"customer": customer,
			"status": "Open",
		}
	)
	project.insert(ignore_permissions=True)
	return project.name


class TestCustomerRequest(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_create_change_request_from_accepted_customer_request(self):
		customer = get_or_create_customer()
		project = create_project(customer)
		customer_request = frappe.get_doc(
			{
				"doctype": "Customer Request",
				"customer": customer,
				"project": project,
				"subject": "_Test Dedicated warehouse dashboard",
				"analysis": "_Test approved analysis",
				"estimated_hours": 12,
				"currency": "PLN",
				"estimated_amount": 2400,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Customer Request", customer_request.name, "workflow_state", "Accepted", update_modified=False
		)
		customer_request.reload()

		change_request_name = customer_request.create_change_request()

		customer_request.reload()
		change_request = frappe.get_doc("Change Request", change_request_name)
		self.assertEqual(customer_request.change_request, change_request.name)
		self.assertEqual(customer_request.workflow_state, "Converted")
		self.assertEqual(change_request.customer_request, customer_request.name)
		self.assertEqual(change_request.project, project)
		self.assertEqual(change_request.approved_hours, 12)
		self.assertEqual(change_request.approved_amount, 2400)

	def test_customer_request_cannot_create_duplicate_change_request(self):
		customer = get_or_create_customer()
		project = create_project(customer)
		customer_request = frappe.get_doc(
			{
				"doctype": "Customer Request",
				"customer": customer,
				"project": project,
				"subject": "_Test Duplicate change request",
				"analysis": "_Test analysis",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Customer Request", customer_request.name, "workflow_state", "Accepted", update_modified=False
		)
		customer_request.reload()

		customer_request.create_change_request()
		customer_request.reload()

		with self.assertRaises(frappe.ValidationError):
			customer_request.create_change_request()

	def test_create_change_request_reloads_latest_customer_request_state(self):
		customer = get_or_create_customer()
		project = create_project(customer)
		customer_request = frappe.get_doc(
			{
				"doctype": "Customer Request",
				"customer": customer,
				"project": project,
				"subject": "_Test Concurrent change request",
				"analysis": "_Test analysis",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Customer Request", customer_request.name, "workflow_state", "Accepted", update_modified=False
		)
		stale_customer_request = frappe.get_doc("Customer Request", customer_request.name)

		existing_change_request = frappe.get_doc(
			{
				"doctype": "Change Request",
				"subject": "_Test Existing change request",
				"customer_request": customer_request.name,
				"customer": customer,
				"project": project,
				"approved_scope": "_Test approved scope",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Customer Request",
			customer_request.name,
			"change_request",
			existing_change_request.name,
			update_modified=False,
		)

		with self.assertRaises(frappe.ValidationError):
			stale_customer_request.create_change_request()

	def test_project_requests_api_returns_project_documents(self):
		customer = get_or_create_customer()
		project = create_project(customer)
		customer_request = frappe.get_doc(
			{
				"doctype": "Customer Request",
				"customer": customer,
				"project": project,
				"subject": "_Test API request",
				"analysis": "_Test API analysis",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Customer Request", customer_request.name, "workflow_state", "Accepted", update_modified=False
		)
		customer_request.reload()
		change_request_name = customer_request.create_change_request()

		result = get_project_requests(project)

		self.assertEqual(result["project"]["name"], project)
		self.assertIn(
			customer_request.name,
			[row.name for row in result["customer_requests"]],
		)
		self.assertIn(
			change_request_name,
			[row.name for row in result["change_requests"]],
		)
