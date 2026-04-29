frappe.ui.form.on("Job Card", {
	refresh(frm) {
		if (frm.doc.priority === "Urgent") {
			frm.page.set_indicator("URGENT", "red");

			frappe.show_alert({
				message: "This Job Card is marked as Urgent",
				indicator: "red",
			});
		}
	},
});
