import datetime

import frappe


@frappe.whitelist()
def share_job_card(job_card_name, user_email):
	if not job_card_name or not user_email:
		frappe.throw("Job Card name and User email are required")

	if not frappe.db.exists("Job Card", job_card_name):
		frappe.throw(f"Job Card '{job_card_name}' does not exist")

	user = frappe.db.get_value("User", {"email": user_email}, "name")
	if not user:
		frappe.throw(f"No user found with email '{user_email}'")

	frappe.share.add(
		doctype="Job Card", name=job_card_name, user=user, read=1, write=0, share=0, everyone=0, notify=1
	)

	return f"Job Card '{job_card_name}' has been shared with {user_email}"


@frappe.whitelist()
def manager_only_method():
	frappe.only_for("QF Manager")
	return "Access granted: You are a QF Manager"


@frappe.whitelist()
def get_job_cards_unsafe():
	return frappe.get_all("Job Card", fields="*")


@frappe.whitelist()
def get_job_cards_safe():
	fields = [
		"name",
		"customer_name",
		"customer_phone",
		"customer_email",
		"device_type",
		"device_model",
		"status",
		"assigned_technician",
		"payment_status",
		"final_amount",
		"delivery_date",
	]
	job_cards = frappe.get_list("Job Card", fields=fields)

	if "QF Manager" not in frappe.get_roles():
		for job_card in job_cards:
			job_card.pop("customer_phone", None)
			job_card.pop("customer_email", None)

	return job_cards


def get_job_card_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)
	if "QF Technician" in user_roles:
		return (
			"exists (select 1 from `tabTechnician` t "
			"where t.name = `tabJob Card`.assigned_technician "
			f"and t.user = {frappe.db.escape(user)})"
		)

	return ""


def has_service_invoice_permission(doc, ptype=None, user=None):
	if user is None:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)
	if "QF Manager" in user_roles:
		return True

	if not doc.get("job_card"):
		return True

	payment_status = frappe.db.get_value("Job Card", doc.job_card, "payment_status")
	return payment_status == "Paid"


def get_overdue_jobs():
	JobCard = frappe.qb.DocType("Job Card")
	cutoff = frappe.utils.now_datetime() - datetime.timedelta(days=7)

	query = (
		frappe.qb.from_(JobCard)
		.select(
			JobCard.name,
			JobCard.customer_name,
			JobCard.assigned_technician,
			JobCard.creation,
		)
		.where(JobCard.status.isin(["Pending Diagnosis", "In Repair"]))
		.where(JobCard.creation < cutoff)
		.orderby(JobCard.creation)
	)

	return query.run(as_dict=True)


def transfer_job(from_tech, to_tech):
	try:
		frappe.db.sql(
			"""
            UPDATE `tabJob Card`
            SET assigned_technician = %s
            WHERE assigned_technician = %s
              AND status NOT IN ('Closed', 'Cancelled')
            """,
			(to_tech, from_tech),
		)
		frappe.db.commit()
	except Exception as exc:
		frappe.db.rollback()
		frappe.log_error(exc)
		raise


def send_job_ready_email(job_card):
	doc = frappe.get_doc("Job Card", job_card)

	subject = f"Job Card {job_card} is Ready for Delivery"
	message = f"""
    Dear {doc.customer_name},

    Your device repair is complete. Job Card {job_card} is ready for delivery.

    Final Amount: {doc.final_amount}
    Delivery Date: {doc.delivery_date or 'TBD'}

    Please visit our service center to collect your device.

    Thank you,
    QuickFix Service Centre
    """

	frappe.sendmail(recipients=[doc.customer_email], subject=subject, message=message)


@frappe.whitelist()
def rename_technician(old_name, new_name):
	frappe.rename_doc("Technician", old_name, new_name, merge=False)
	return f"Technician renamed from '{old_name}' to '{new_name}'. Linked Job Cards updated automatically."


# Note on merge=True danger:
# merge=True in frappe.rename_doc() merges the old document into the new one if the new_name already exists.
# This is dangerous because it can lead to data loss or corruption:
# - If the target document exists, all data from the old document is merged into it, potentially overwriting fields.
# - References to the old document are updated to point to the target, but if the merge logic fails, data can be lost.
# - It's risky when renaming to an existing name, as it combines records unexpectedly.
# - Use merge=True only when intentionally merging two existing records, not for simple renames.
