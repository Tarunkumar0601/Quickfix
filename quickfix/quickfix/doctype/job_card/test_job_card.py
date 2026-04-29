# Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestJobCard(FrappeTestCase):
	def test_base_validations_run_on_save(self):
		job_card = frappe.get_doc(
			{
				"doctype": "Job Card",
				"customer_name": "Test Customer",
				"customer_phone": "12345",  # Invalid: only 5 digits
				"problem_description": "Test job",
				"priority": "Normal",
				"status": "Pending Diagnosis",
			}
		)

		with self.assertRaises(frappe.ValidationError) as cm:
			job_card.insert()

		self.assertIn("Customer Phone must contain exactly 10 digits", str(cm.exception))

	def test_totals_calculated_on_validate(self):
		job_card = frappe.get_doc(
			{
				"doctype": "Job Card",
				"customer_name": "Test Customer",
				"customer_phone": "1234567890",
				"device_type": "laptop",
				"problem_description": "Test job with parts",
				"priority": "Normal",
				"status": "Pending Diagnosis",
				"labour_charge": 100,
				"parts_used": [
					{
						"part": "Test Part",  # Assuming this exists or will be mocked
						"quantity": 2,
						"unit_price": 50,
					}
				],
			}
		)

		job_card.insert()

		job_card.reload()

		self.assertEqual(job_card.parts_total, 100)
		self.assertEqual(job_card.final_amount, 200)
