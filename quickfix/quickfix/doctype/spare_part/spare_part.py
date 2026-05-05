# Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class SparePart(Document):
	def autoname(self):
		if self.part_code:
			prefix = self.part_code.upper()
			series = make_autoname("PART-.YYYY-.####")
			self.name = f"{prefix}-{series}"

	def validate(self):
		if self.unit_cost is None or self.selling_price is None:
			frappe.throw("Unit Cost and Selling Price are required")

		if self.selling_price <= self.unit_cost:
			frappe.throw("Selling Price must be greater than Unit Cost")

	def on_update(self):
		settings = frappe.get_single("QuickFix Settings")
		if not getattr(settings, "low_stock_alert_enabled", 0):
			return

		threshold = self.reorder_level or 0

		if (self.stock_qty or 0) <= threshold:
			frappe.logger().warning(
				f"Low stock detected for Spare Part {self.name}: "
				f"stock_qty={(self.stock_qty or 0)}, threshold={threshold}"
			)
