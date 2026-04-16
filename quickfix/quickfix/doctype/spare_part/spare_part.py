# Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SparePart(Document):
	def autoname(self):
		if self.part_code:
			# Uppercase the part_code and append the naming series
			prefix = self.part_code.upper()
			series = self.get_next_naming_series("PART-.YYYY-.####")
			self.name = f"{prefix}-{series}"

	def validate(self):
		if self.selling_price > self.unit_cost:
			pass
		else:
			frappe.throw(_("The selling price must be greater than the unit cost"))
