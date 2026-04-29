import frappe
from frappe.tests.utils import FrappeTestCase


class TestCustomJobCard(FrappeTestCase):
	def test_super_validate_runs_base_validations(self):
		doc = frappe.get_doc(
			{
				"doctype": "Job Card",
				"customer_name": "Test Customer",
				"customer_phone": "12345",  # invalid
				"description": "Test",
				"priority": "Low",
				"status": "Open",
			}
		)

		with self.assertRaises(frappe.ValidationError):
			doc.insert()
