import frappe


def send_urgent_alert(job_card, manager):
	subject = f"Urgent Job Card {job_card} has no assigned technician"
	message = (
		f"Job Card {job_card} is marked as Urgent but has no assigned technician. "
		"Please assign a technician immediately."
	)
	frappe.sendmail(recipients=[manager], subject=subject, message=message)
