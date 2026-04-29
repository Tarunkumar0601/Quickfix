# Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data()
	chart = None
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"label": _("Part Name"),
			"fieldname": "part_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Part Code"),
			"fieldname": "part_code",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Device Type"),
			"fieldname": "compatible_device_type",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Stock Qty"),
			"fieldname": "stock_qty",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Reorder Level"),
			"fieldname": "reorder_level",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Unit Cost"),
			"fieldname": "unit_cost",
			"fieldtype": "Currency",
			"precision": 2,
			"width": 120,
		},
		{
			"label": _("Selling Price"),
			"fieldname": "selling_price",
			"fieldtype": "Currency",
			"precision": 2,
			"width": 130,
		},
		{
			"label": _("Margin %"),
			"fieldname": "margin_percent",
			"fieldtype": "Percent",
			"precision": 2,
			"width": 110,
		},
		{
			"label": _("Total Value"),
			"fieldname": "total_value",
			"fieldtype": "Currency",
			"precision": 2,
			"width": 130,
		},
	]


def get_data():
	rows = frappe.get_list(
		"Spare Part",
		fields=[
			"part_name",
			"part_code",
			"compatible_device_type",
			"stock_qty",
			"reorder_level",
			"unit_cost",
			"selling_price",
		],
		order_by="part_name asc",
		limit_page_length=0,
	)

	data = []
	total_stock = 0
	grand_total_value = 0

	for row in rows:
		stock_qty = flt(row.stock_qty)
		unit_cost = flt(row.unit_cost)
		selling_price = flt(row.selling_price)

		margin = 0
		if unit_cost:
			margin = ((selling_price - unit_cost) / unit_cost) * 100

		total_value = stock_qty * unit_cost

		data.append(
			{
				"part_name": row.part_name,
				"part_code": row.part_code,
				"compatible_device_type": row.compatible_device_type,
				"stock_qty": stock_qty,
				"reorder_level": flt(row.reorder_level),
				"unit_cost": round(unit_cost, 2),
				"selling_price": round(selling_price, 2),
				"margin_percent": round(margin, 2),
				"total_value": round(total_value, 2),
			}
		)

		total_stock += stock_qty
		grand_total_value += total_value

	# Total row
	data.append(
		{
			"part_name": _("Total"),
			"stock_qty": total_stock,
			"total_value": round(grand_total_value, 2),
		}
	)

	return data


def get_report_summary(data):
	rows = [d for d in data if d.get("part_name") != "Total"]

	total_parts = len(rows)

	below_reorder = len([d for d in rows if flt(d["stock_qty"]) <= flt(d["reorder_level"])])

	total_inventory_value = sum(flt(d["total_value"]) for d in rows)

	return [
		{
			"label": _("Total Parts"),
			"value": total_parts,
			"indicator": "Blue",
		},
		{
			"label": _("Below Reorder"),
			"value": below_reorder,
			"indicator": "Red" if below_reorder else "Green",
		},
		{
			"label": _("Total Inventory Value"),
			"value": round(total_inventory_value, 2),
			"datatype": "Currency",
			"indicator": "Green",
		},
	]
