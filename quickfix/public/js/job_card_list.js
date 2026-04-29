frappe.listview_settings["Job Card"] = {
	add_fields: ["final_amount", "priority", "status"],
	has_indicator_for_cancelled: true,
	has_indicator_for_draft: true,
	get_indicator(doc) {
		if (doc.status === "Draft") {
			return ["Draft", "darkgrey", "status,=,Draft"];
		}

		if (doc.status === "Pending Diagnosis") {
			return ["Pending Diagnosis", "orange", "status,=,Pending Diagnosis"];
		}

		if (doc.status === "Awaiting Customer Approval") {
			return ["Awaiting Customer Approval", "yellow", "status,=,Awaiting Customer Approval"];
		}

		if (doc.status === "In Repair") {
			return ["In Repair", "blue", "status,=,In Repair"];
		}

		if (doc.status === "Ready for Delivery") {
			return ["Ready for Delivery", "green", "status,=,Ready for Delivery"];
		}

		if (doc.status === "Delivered") {
			return ["Delivered", "gray", "status,=,Delivered"];
		}

		if (doc.status === "Cancelled") {
			return ["Cancelled", "red", "status,=,Cancelled"];
		}

		return [doc.status || "Draft", "darkgrey"];
	},
	formatters: {
		final_amount(value) {
			if (!value) return "₹0";
			return `<span style="font-weight:600;color:#1f7a1f;">${format_currency(
				value,
				"INR"
			)}</span>`;
		},

		priority(value) {
			if (!value) return "";

			const colors = {
				Low: "gray",
				Medium: "orange",
				High: "red",
				Urgent: "purple",
			};

			return `<span style="font-weight:600;color:${
				colors[value] || "black"
			};">${value}</span>`;
		},
	},
	button: {
		show(doc) {
			return doc.status === "In Repair";
		},

		get_label() {
			return __("Complete Repair");
		},

		get_description(doc) {
			return __("Mark {0} as Ready for Delivery", [doc.name]);
		},

		action(doc) {
			frappe.call({
				method: "frappe.client.set_value",
				args: {
					doctype: "Job Card",
					name: doc.name,
					fieldname: "status",
					value: "Ready for Delivery",
				},
				callback() {
					frappe.show_alert({
						message: `${doc.name} updated`,
						indicator: "green",
					});
					cur_list.refresh();
				},
			});
		},
	},
};
