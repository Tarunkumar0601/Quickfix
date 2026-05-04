import frappe
from frappe.utils import getdate


def generate_monthly_revenue_report(year):
	months = range(1, 13)

	results = []

	for i, month in enumerate(months, 1):
		start = getdate(f"{year}-{month:02d}-01")

		if month == 12:
			end = getdate(f"{year+1}-01-01")
		else:
			end = getdate(f"{year}-{month+1:02d}-01")

		revenue = frappe.db.sql(
			"""
            SELECT COALESCE(SUM(final_amount), 0)
            FROM `tabJob Card`
            WHERE status = 'Delivered'
              AND payment_status = 'Paid'
              AND creation >= %s AND creation < %s
        """,
			(start, end),
		)[0][0]

		results.append({"month": month, "revenue": revenue})

		percent = round(i / 12 * 100)

		frappe.publish_progress(
			percent=percent, title="Generating Revenue Report", description=f"Processed month {month}/12"
		)

	frappe.cache().set_value(f"revenue_report_{year}", results, expires_in_sec=3600)

	return results
