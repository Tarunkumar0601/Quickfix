# Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PartUsageEntry(Document):
	def validate(self):
		self.total_price = (self.unit_price or 0) * (self.quantity or 0)
