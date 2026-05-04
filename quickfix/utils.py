import base64
from io import BytesIO

import frappe
import qrcode


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


@frappe.whitelist()
def get_qr_base64(data):
	qr = qrcode.make(data)

	buffer = BytesIO()
	qr.save(buffer, format="PNG")

	img_str = base64.b64encode(buffer.getvalue()).decode()

	return img_str
