import frappe
from frappe.utils import now_datetime


def log_change(doc, method=None):
	if doc.doctype == "Audit Log":
		return

	action_map = {
		"on_update": "Save",
		"on_submit": "Submit",
		"on_cancel": "Cancel",
	}

	audit_log = frappe.get_doc(
		{
			"doctype": "Audit Log",
			"doctype_name": doc.doctype,
			"document_name": doc.name,
			"action": action_map.get(method, method or "Unknown"),
			"user": frappe.session.user,
			"timestamp": now_datetime(),
		}
	)
	audit_log.insert()
