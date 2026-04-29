# Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, getdate, today

COMPLETED_STATUSES = {"Ready for Delivery", "Delivered"}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	filters = normalize_filters(filters)

	device_types = get_device_types()
	columns = get_columns(filters, device_types)
	data = get_data(filters, device_types)
	chart = get_chart_data(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def normalize_filters(filters):
	if not filters.get("to_date"):
		filters.to_date = today()

	if not filters.get("from_date"):
		filters.from_date = add_days(filters.to_date, -30)

	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date."))

	return filters


def get_columns(filters=None, device_types=None):
	device_types = device_types or get_device_types()
	columns = [
		{
			"label": _("Technician"),
			"fieldname": "technician",
			"fieldtype": "Link",
			"options": "Technician",
			"width": 180,
		},
		{
			"label": _("Total Jobs"),
			"fieldname": "total_jobs",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"label": _("Completed"),
			"fieldname": "completed",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Avg Turnaround Days"),
			"fieldname": "avg_turnaround_days",
			"fieldtype": "Float",
			"precision": 2,
			"width": 160,
		},
		{
			"label": _("Revenue"),
			"fieldname": "revenue",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Completion Rate %"),
			"fieldname": "completion_rate",
			"fieldtype": "Percent",
			"precision": 2,
			"width": 140,
		},
	]

	for device_type in device_types:
		columns.append(
			{
				"label": device_type.name,
				"fieldname": frappe.scrub(device_type.name),
				"fieldtype": "Int",
				"width": 100,
			}
		)

	return columns


def get_data(filters=None, device_types=None):
	device_types = device_types or get_device_types()
	job_cards = get_job_cards(filters)
	device_field_map = {device_type.name: frappe.scrub(device_type.name) for device_type in device_types}
	rows_by_technician = {}

	for job_card in job_cards:
		technician = job_card.assigned_technician
		if technician not in rows_by_technician:
			rows_by_technician[technician] = make_row(technician, device_field_map.values())

		row = rows_by_technician[technician]
		row["total_jobs"] += 1

		device_fieldname = device_field_map.get(job_card.device_type)
		if device_fieldname:
			row[device_fieldname] += 1

		if is_completed(job_card.status):
			row["completed"] += 1
			row["revenue"] += flt(job_card.final_amount)

			if job_card.delivery_date:
				row["_turnaround_total"] += max(
					date_diff(getdate(job_card.delivery_date), getdate(job_card.creation)),
					0,
				)
				row["_turnaround_count"] += 1

	data = []
	for row in rows_by_technician.values():
		row["avg_turnaround_days"] = (
			round(row["_turnaround_total"] / row["_turnaround_count"], 2) if row["_turnaround_count"] else 0
		)
		row["completion_rate"] = (
			round((row["completed"] / row["total_jobs"]) * 100, 2) if row["total_jobs"] else 0
		)
		row["revenue"] = round(row["revenue"], 2)
		row.pop("_turnaround_total", None)
		row.pop("_turnaround_count", None)
		data.append(row)

	return sorted(data, key=lambda row: (-row["completed"], -row["revenue"], row["technician"]))


def get_job_cards(filters):
	job_card_filters = [
		["assigned_technician", "is", "set"],
		["creation", ">=", filters.from_date],
		["creation", "<", add_days(filters.to_date, 1)],
	]

	if filters.get("technician"):
		job_card_filters.append(["assigned_technician", "=", filters.technician])

	return frappe.get_list(
		"Job Card",
		filters=job_card_filters,
		fields=[
			"name",
			"assigned_technician",
			"device_type",
			"status",
			"creation",
			"delivery_date",
			"final_amount",
		],
		order_by="assigned_technician asc, creation asc",
		limit_page_length=0,
	)


def get_device_types():
	return frappe.get_all("Device Type", fields=["name"], order_by="name asc")


def make_row(technician, device_fieldnames):
	row = {
		"technician": technician,
		"total_jobs": 0,
		"completed": 0,
		"avg_turnaround_days": 0,
		"revenue": 0.0,
		"completion_rate": 0.0,
		"_turnaround_total": 0,
		"_turnaround_count": 0,
	}

	for fieldname in device_fieldnames:
		row[fieldname] = 0

	return row


def is_completed(status):
	return status in COMPLETED_STATUSES


def get_chart_data(data):
	if not data:
		return None

	return {
		"data": {
			"labels": [row["technician"] for row in data],
			"datasets": [
				{"name": _("Total Jobs"), "values": [row["total_jobs"] for row in data]},
				{"name": _("Completed"), "values": [row["completed"] for row in data]},
			],
		},
		"type": "bar",
		"colors": ["#7cd6fd", "#36a64f"],
	}


def get_report_summary(data):
	total_jobs = sum(row["total_jobs"] for row in data)
	total_revenue = round(sum(row["revenue"] for row in data), 2)
	best_technician = get_best_technician(data)

	return [
		{
			"value": total_jobs,
			"label": _("Total Jobs"),
			"datatype": "Int",
			"indicator": "blue",
		},
		{
			"value": total_revenue,
			"label": _("Total Revenue"),
			"datatype": "Currency",
			"indicator": "green",
		},
		{
			"value": best_technician or _("N/A"),
			"label": _("Best Technician"),
			"datatype": "Data",
			"indicator": "orange" if best_technician else "gray",
		},
	]


def get_best_technician(data):
	if not data:
		return None

	best_row = max(
		data,
		key=lambda row: (row["completed"], row["completion_rate"], row["revenue"]),
	)
	return best_row["technician"]
