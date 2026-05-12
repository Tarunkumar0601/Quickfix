import frappe
from frappe.utils import today


def check_low_stock():
	try:
		frappe.get_doc({"doctype": "Audit Log", "action": "low_stock_check", "date": today()}).insert()

	except frappe.DuplicateEntryError:
		return
