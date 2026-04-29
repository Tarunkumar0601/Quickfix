import frappe


def send_urgent_alert(job_card, manager):
	subject = f"Urgent Job Card {job_card} has no assigned technician"
	message = (
		f"Job Card {job_card} is marked as Urgent but has no assigned technician. "
		"Please assign a technician immediately."
	)
	frappe.sendmail(recipients=[manager], subject=subject, message=message)


def get_shop_name():
	settings = frappe.get_single("QuickFix Settings")
	return settings.shop_name or "QuickFix"


def format_job_id(value):
	if not value:
		return ""
	return f"JOB#{value}"
