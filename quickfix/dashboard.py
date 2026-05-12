import frappe
from frappe import _
from frappe.utils import flt, today
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
def get_today_delivered_revenue(filters=None):
	filters = frappe.parse_json(filters) or []
	filters.extend(
		[
			["Job Card", "status", "=", "Delivered"],
			["Job Card", "delivery_date", "=", today()],
			["Job Card", "docstatus", "!=", 2],
		]
	)

	total = (
		frappe.get_all(
			"Job Card",
			filters=filters,
			fields=["sum(final_amount) as total"],
		)[0].total
		or 0
	)

	return {"value": flt(total), "route": ["List", "Job Card", "List"]}


@frappe.whitelist()
def get_status_chart_data():
	cache_key = "quickfix:status_chart"
	cached = frappe.cache.get_value(cache_key)
	if cached:
		return cached

	rows = frappe.db.get_all(
		"Job Card", fields=["status", "count(name) as count"], group_by="status", order_by="status asc"
	)
	labels = []
	values = []
	for row in rows:
		labels.append(row.status or "Unknown")
		values.append(row.count)

	chart_data = {
		"labels": labels,
		"datasets": [
			{
				"name": _("Job Count"),
				"values": values,
			}
		],
		"type": "bar",
	}

	frappe.cache.set_value(
		cache_key,
		chart_data,
		expires_in_sec=300,
	)

	return chart_data
