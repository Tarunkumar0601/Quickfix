# Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# from quickfix.job_card_event_demo import controller_validate


class JobCard(Document):
	def validate(self):
		# controller_validate(self)
		self.auto_update_status()
		self.validate_customer_phone()
		self.validate_technician_assignment()
		self.set_default_labour_charge()
		self.calculate_totals()

	def validate_customer_phone(self):
		if not self.customer_phone:
			frappe.throw("Customer Phone is required")

		phone_digits = "".join(c for c in self.customer_phone if c.isdigit())
		if len(phone_digits) != 10:
			frappe.throw("Customer Phone must contain exactly 10 digits")

	def validate_technician_assignment(self):
		repair_statuses = ["In Repair", "Ready for Delivery", "Delivered"]
		if self.status in repair_statuses and not self.assigned_technician:
			frappe.throw(f"Assigned Technician is required when Job Card status is '{self.status}'")

	def set_default_labour_charge(self):
		if not self.labour_charge:
			settings = frappe.get_single("QuickFix Settings")
			self.labour_charge = settings.default_labour_charge or 0

	def calculate_totals(self):
		parts_total = 0
		if self.parts_used:
			for part in self.parts_used:
				unit_price = part.unit_price or 0
				quantity = part.quantity or 0
				part.total_price = unit_price * quantity
				parts_total += part.total_price

		self.parts_total = parts_total

		self.final_amount = (self.parts_total or 0) + (self.labour_charge or 0)

	def before_submit(self):
		if self.status != "Ready for Delivery":
			frappe.throw(
				f"Job Card can only be submitted when status is 'Ready for Delivery', "
				f"but current status is '{self.status}'"
			)

		if self.parts_used:
			for idx, part in enumerate(self.parts_used, start=1):
				spare_part_name = part.part
				quantity = part.quantity or 0

				stock_qty = frappe.db.get_value("Spare Part", spare_part_name, "stock_qty")

				if stock_qty is None:
					frappe.throw(f"Spare Part '{spare_part_name}' not found in row {idx}")

				if stock_qty < quantity:
					frappe.throw(
						f"Insufficient stock for '{spare_part_name}' in row {idx}: "
						f"required {quantity}, but only {stock_qty} available"
					)

	def on_submit(self):
		if self.parts_used:
			for part in self.parts_used:
				spare_part_name = part.part
				quantity = part.quantity or 0

				current_stock = frappe.db.get_value("Spare Part", spare_part_name, "stock_qty") or 0
				new_stock = current_stock - quantity

				# ignore_permissions=True is acceptable here because this is a system-initiated
				# stock deduction triggered by Job Card submission, not a direct user action.
				# This ensures the system can update inventory without requiring explicit user permissions.
				frappe.db.set_value(
					"Spare Part", spare_part_name, "stock_qty", new_stock, ignore_permissions=True
				)

		service_invoice = frappe.get_doc(
			{
				"doctype": "Service Invoice",
				"job_card": self.name,
				"invoice_date": frappe.utils.today(),
				"labour_charge": self.labour_charge,
				"parts_total": self.parts_total,
				"total_amount": self.final_amount,
				"payment_status": "Unpaid",
			}
		)
		service_invoice.insert(ignore_permissions=True)

		frappe.publish_realtime(
			"job_ready",
			{"job_card": self.name, "customer_name": self.customer_name, "final_amount": self.final_amount},
			user=self.owner,
		)

		frappe.enqueue("quickfix.api.send_job_ready_email", job_card=self.name, queue="short")

	def on_cancel(self):
		self.status = "Cancelled"

		if self.parts_used:
			for part in self.parts_used:
				spare_part_name = part.part
				quantity = part.quantity or 0

				current_stock = frappe.db.get_value("Spare Part", spare_part_name, "stock_qty") or 0
				new_stock = current_stock + quantity

				frappe.db.set_value(
					"Spare Part", spare_part_name, "stock_qty", new_stock, ignore_permissions=True
				)

		service_invoice_name = frappe.db.get_value("Service Invoice", {"job_card": self.name}, "name")
		if service_invoice_name:
			service_invoice = frappe.get_doc("Service Invoice", service_invoice_name)
			service_invoice.cancel()

	def on_trash(self):
		if self.status not in ["Cancelled", "Draft"]:
			frappe.throw(
				f"Cannot delete Job Card with status '{self.status}'. "
				"Only Job Cards with status 'Cancelled' or 'Draft' can be deleted."
			)

	# def on_update(self):
	# 	if not getattr(self, "_updating_status", False):
	# 		self._updating_status = True
	# 		if self.status == "Draft" and self.assigned_technician:
	# 			self.status = "Pending Diagnosis"
	# 		self._updating_status = False

	def auto_update_status(self):
		if self.status == "Draft" and self.assigned_technician:
			self.status = "Pending Diagnosis"
