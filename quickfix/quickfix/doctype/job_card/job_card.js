// Copyright (c) 2026, 12, First Floor, 1st East Cross, Sundarapuram, Tiruppur. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Card", {
	onload(frm) {
		frappe.realtime.on("job_ready", function (data) {
			if (data && data.name === frm.doc.name) {
				frappe.show_alert({
					message: `Job Card ${frm.doc.name}is ready for delivery`,
					indicator: "green",
				});
			}
		});
	},

	setup(frm) {
		frm.set_query("assigned_technician", function () {
			return {
				filters: {
					status: "Active",
					specialization: frm.doc.device_type,
				},
			};
		});
	},

	refresh(frm) {
		add_status_indicator(frm);
		add_delivery_button(frm);
		add_transfer_button(frm);
		add_rejection_button(frm);
		show_shop_name(frm);
	},

	assigned_technician(frm) {
		if (!frm.doc.assigned_technician) return;
		frappe.db
			.get_value("Technician", frm.doc.assigned_technician, "specialization")
			.then((r) => {
				const specialization = r.message.specialization;
				if (
					frm.doc.device_type &&
					specialization &&
					specialization !== frm.doc.device_type
				) {
					frappe.msgprint({
						title: "Specialization Mismatch",
						message: "Selected technician specialization does not match device type.",
						indicator: "orange",
					});
				}
			});
	},
});

frappe.ui.form.on("Part", {
	quantity(frm, cdt, cdn) {
		update_part_total(cdt, cdn);
	},

	unit_price(frm, cdt, cdn) {
		update_part_total(cdt, cdn);
	},
});

function update_part_total(cdt, cdn) {
	let row = locals[cdt][cdn];
	let qty = flt(row.quantity || 0);
	let price = flt(row.unit_price || 0);
	let total = qty * price;

	frappe.model.set_value(cdt, cdn, "total_price", total);
}

function add_status_indicator(frm) {
	frm.dashboard.clear_headline();
	const status = frm.doc.status;
	if (status === "Pending Diagnosis") {
		frm.dashboard.add_indicator("Pending Diagnosis", "orange");
	} else if (status === "In Repair") {
		frm.dashboard.add_indicator("In Progress", "blue");
	} else if (status === "Ready for Delivery") {
		frm.dashboard.add_indicator("Ready for Delivery", "green");
	} else if (status === "Delivered") {
		frm.dashboard.add_indicator("Delivered", "gray");
	}
}

function add_delivery_button(frm) {
	if (frm.doc.status === "Ready for Delivery" && frm.doc.docstatus === 1) {
		frm.add_custom_button("Mark as Delivered", function () {
			frm.set_value("status", "Delivered");
		});
	}
}

function show_shop_name(frm) {
	const shopName = frappe.boot.quickfix_shop_name;
	if (shopName) {
		frm.page.set_indicator(shopName, "blue");
	}
}

function add_rejection_button(frm) {
	if (!frm.is_new() && frm.doc.docstatus === 0) {
		frm.add_custom_button(
			"Reject Job",
			function () {
				show_reject_value(frm);
			},
			"Actions"
		);
	}
}

function show_reject_value(frm) {
	const d = new frappe.ui.Dialog({
		title: "Reject Job Card",
		fields: [
			{
				label: "Rejection Reason",
				fieldname: "rejection_reason",
				fieldtype: "Small Text",
				reqd: 1,
			},
		],
		primary_action_label: "Reject",
		primary_action(values) {
			frm.set_value("status", "Cancelled");
			frm.set_value("rejection_reason", values.rejection_reason);

			frm.save().then(() => {
				frappe.show_alert({
					message: "Job Card Rejected",
					indicator: "red",
				});
				d.hide();
			});
		},
	});
	d.show();
}

function add_transfer_button(frm) {
	if (!frm.is_new() && frm.doc.docstatus === 0) {
		frm.add_custom_button(
			"Transfer Technician",
			function () {
				transfer_technician(frm);
			},
			"Actions"
		);
	}
}

function transfer_technician(frm) {
	frappe.prompt(
		[
			{
				label: "New Technician",
				fieldname: "new_technician",
				fieldtype: "Link",
				options: "Technician",
				reqd: 1,
				get_query: function () {
					return {
						filters: {
							status: "Active",
							specialization: frm.doc.device_type,
						},
					};
				},
			},
		],
		function (values) {
			frappe.confirm(
				`Transfer this job to technician <b>${values.new_technician}</b>?`,
				function () {
					frappe.call({
						method: "quickfix.api.transfer_technician",
						args: {
							job_card: frm.doc.name,
							technician: values.new_technician,
						},
						freeze: true,
						freeze_message: "Transferring Job...",
						callback: function (r) {
							if (!r.exc) {
								frm.reload_doc().then(() => {
									frm.trigger("assigned_technician");
									frappe.show_alert({
										message: "Technician transferred successfully",
										indicator: "green",
									});
								});
								frm.reload_doc();
							}
						},
					});
				}
			);
		},
		"Transfer Technician",
		"Transfer"
	);
}
