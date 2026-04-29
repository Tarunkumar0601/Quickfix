// Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
// For license information, please see license.txt

// quickfix/quickfix/report/spare_parts_inventory/spare_parts_inventory.js

frappe.query_reports["Spare Parts Inventory"] = {
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Skip total row
		if (!data || data.part_name === "Total") {
			return value;
		}

		// Red background if stock below reorder level
		if (flt(data.stock_qty) <= flt(data.reorder_level)) {
			value = `
                <span style="
                    background:#ffe5e5;
                    color:#a10000;
                    padding:2px 4px;
                    border-radius:4px;
                    font-weight:600;
                ">
                    ${value}
                </span>
            `;
		}

		return value;
	},
};
