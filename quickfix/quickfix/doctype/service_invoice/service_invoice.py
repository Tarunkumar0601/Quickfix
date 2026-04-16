# Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ServiceInvoice(Document):
	def validate(self):
		self.invoice_number = self.name
		self.calculate_totals()

	def calculate_totals(self):
		if self.job_card:
			job_card = frappe.get_doc("Job Card", self.job_card)
			self.parts_total = job_card.parts_total or 0
			self.labour_charge = job_card.labour_charge or 0
			self.total_amount = (self.parts_total or 0) + (self.labour_charge or 0)
