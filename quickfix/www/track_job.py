import re

import frappe


def get_context(context):
	context.title = "Track Repair Job"
	context.description = "Track your QuickFix repair job status online."
	context.og_title = "QuickFix Job Tracking"

	context.phone = ""
	context.jobs = []

	phone = frappe.form_dict.get("phone", "").strip()

	if phone:
		phone = re.sub(r"\D", "", phone)
		context.phone = phone

		if len(phone) >= 10:
			context.jobs = frappe.db.sql(
				"""
                SELECT name, status, device_brand,
                       device_model, customer_name,
                       customer_phone, modified
                FROM `tabJob Card`
                WHERE customer_phone = %s
                ORDER BY modified DESC
                LIMIT 10
            """,
				(phone,),
				as_dict=True,
			)
