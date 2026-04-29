import frappe
from frappe import _

from quickfix.monkey_patches import apply_all


def after_install():
	create_default_device_type()
	create_default_settings()
	apply_all()
	frappe.msgprint("QuickFix app installed successfully. Default setup Completed and monkey patches applied")


def create_default_device_type():
	devices_types = ["Mobile", "Laptop", "Tablet"]
	for device_type_name in devices_types:
		if not frappe.db.exists("Device Type", device_type_name):
			doc = frappe.get_doc({"doctype": "Device Type", "device_type": device_type_name})
			doc.insert(ignore_permission=True)
	frappe.db.commit()


def create_default_settings():
	if not frappe.db.exists("QuickFix Settings", "QuickFix Settings"):
		settings = frappe.get_doc(
			{
				"doctype": "QuickFix Settings",
				"name": "QuickFix Settings",
				"default_labour_charge": 500,
				"low_stock_alert_enabled": 1,
			}
		)
		settings.insert(ignore_permission=True)
	frappe.db.commit()


def after_uninstall():
	submitted_job_cards = frappe.db.count("Job Card", {"docstatus": 1})

	if submitted_job_cards > 0:
		frappe.throw(
			_(
				"Cannot uninstall QuickFix app because submitted Job Cards exist. "
				"Please cancel/delete submitted records before uninstalling."
			),
			frappe.ValidationError,
		)
