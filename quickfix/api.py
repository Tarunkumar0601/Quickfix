import datetime
import hashlib
import hmac
import json
import traceback

import frappe
import requests
from frappe import _
from frappe.utils import now


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

	if user == "Administrator":
		return ""

	user_roles = frappe.get_roles(user)

	if "System Manager" in user_roles:
		return ""
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
	except Exception as exc:
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


@frappe.whitelist()
def custom_get_count(doctype, filters=None, debug=False, cache=False):
	log = frappe.get_doc(
		{
			"doctype": "Audit Log",
			"document_name": f"AUDIT-{frappe.generate_hash(length=8)}",
			"doctype_name": doctype,
			"action": "count_queried",
			"user": frappe.session.user,
			"timestamp": now(),
		}
	)

	log.insert()

	from frappe.client import get_count

	return get_count(doctype, filters, debug, cache)


@frappe.whitelist()
def transfer_technician(job_card, technician):
	doc = frappe.get_doc("Job Card", job_card)
	doc.assigned_technician = technician
	doc.save()

	return {"message": "Transferred successfully"}


@frappe.whitelist()
def queue_technician_performance_report(filters=None):
	filters = json.loads(filters) if isinstance(filters, str) else (filters or {})
	prepared = frappe.get_doc(
		{
			"doctype": "Prepared Report",
			"report_name": "Technician Performance Report",
			"filters": frappe.as_json(filters),
			"owner": frappe.session.user,
			"status": "Queued",
		}
	).insert()

	frappe.enqueue(
		"quickfix.api.run_technician_performance_report",
		queue="long",
		timeout=1200,
		prepared_report=prepared.name,
		filters=filters,
	)

	return {"message": _("Report queued successfully"), "prepared_report": prepared.name}


def run_technician_performance_report(prepared_report, filters=None):
	try:
		pr = frappe.get_doc("Prepared Report", prepared_report)
		pr.status = "Running"
		pr.save()
		report = frappe.get_doc("Report", "Technician Performance Report")
		result = report.execute_script_report(filters or {})
		pr.report_end_time = frappe.utils.now()
		pr.status = "Completed"
		pr.report_data = frappe.as_json(result)
		pr.save()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Prepared Technician Performance Report Failed")
		pr = frappe.get_doc("Prepared Report", prepared_report)
		pr.status = "Error"
		pr.error_message = traceback.format_exc()
		pr.save()


logger = frappe.logger("quickfix")


@frappe.whitelist()
def send_webhook(job_card_name, retry_count=0):
	settings = frappe.get_single("QuickFix Settings")

	if not settings.webhook_url:
		return
	doc = frappe.get_doc("Job Card", job_card_name)

	raw = f"{doc.name}-job_submitted"
	webhook_id = hashlib.sha256(raw.encode()).hexdigest()

	already_sent = frappe.db.exists(
		"Audit Log",
		{
			"document_name": webhook_id,
			"action": "webhook_sent",
		},
	)

	if already_sent:
		logger.info(f"Skipping duplicate webhook for {doc.name}")
		return

	payload = {
		"event": "job_submitted",
		"job_card": doc.name,
		"customer": doc.customer_name,
		"amount": doc.final_amount,
	}

	try:
		response = requests.post(
			settings.webhook_url,
			json=payload,
			timeout=5,
		)

		response.raise_for_status()

		frappe.get_doc(
			{
				"doctype": "Audit Log",
				"doctype_name": "Job Card",
				"document_name": "webhook_id",
				"action": "webhook_sent",
				"user": frappe.session.user,
				"timestamp": now(),
			}
		).insert()

	except Exception as e:
		frappe.get_doc(
			{
				"doctype": "Audit Log",
				"doctype_name": "Job Card",
				"document_name": "webhook_id",
				"action": "webhook_failed",
				"user": frappe.session.user,
				"timestamp": now(),
			}
		).insert()

		frappe.log_error(
			title="Webhook Error",
			message=f"""
			webhook failed for Job Card: {doc.name}

			Retry Count: {retry_count}

			Error:
			{e!s}
			""",
		)

		if retry_count < 3:
			frappe.enqueue(
				"quickfix.api.send_webhook",
				job_card_name=job_card_name,
				retry_count=retry_count + 1,
				enqueque_after_commit=True,
			)
		else:
			logger.error(f"Wbhook permanently failed for {doc.name}")


@frappe.whitelist(allow_guest=True)
def payment_webhook():
	payload = frappe.request.data
	if not payload:
		frappe.throw("Empty Payload")

	secret = frappe.conf.get("payment_webhook_secret", "")
	signature = frappe.get_request_header("X-siganture")
	expected_signature = hmac.new(
		secret.encode(),
		payload,
		hashlib.sha256,
	).hexdigest()

	logger.info(f"RAW PAYLOAD: {payload}")
	logger.info(f"EXPECTED: {expected_signature}")
	logger.info(f"RECEIVED: {signature}")

	if not hmac.compare_digest(expected_signature, signature or ""):
		frappe.throw(
			"Invalid Signature",
			frappe.AuthenticationError,
		)

	data = json.loads(payload)

	already_processed = frappe.db.exists(
		"Audit Log",
		{"action": "payment_received", "webhook_id": data["ref"]},
	)

	if already_processed:
		return {
			"status": "duplicate",
			"message": "Already processed",
		}

	if data.get("invoice"):
		invoice = frappe.get_doc("Service Inovice", data["invoice"])

		invoice.payment_status = "Paid"
		invoice.save()
	if data.get("job card"):
		frappe.db.set_value(
			"Job Card",
			data["job_card"],
			"payment_status",
			"Paid",
		)

	frappe.get_doc(
		{
			"doctype": "Audit Log",
			"doctype_name": "Service Invoice",
			"document_name": data.get("invoice") or data.get("job_card"),
			"action": "payment_received",
			"user": "Guest",
			"timestamp": now(),
		}
	).insert()

	return {
		"status": "ok",
		"message": "Payment processed successfully",
	}


@frappe.whitelist()
def trigger_failed_job():
	frappe.enqueue("quickfix.api.failing_background_job", queue="default")

	return "Failing job queued"


def failing_background_job():
	logger = frappe.logger("quickfix")
	logger.info("Starting failing background job")
	raise Exception("Intentional background job failure for testing")
