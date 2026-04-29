const technicianPerformanceCurrentMonthReports = new Set([
	"Technician Performance - This Month",
	"Technician performance - This month",
]);

function isCurrentMonthTechnicianPerformanceReport(queryReport) {
	const currentReportName = queryReport?.report_name || frappe.get_route?.()[1];

	return technicianPerformanceCurrentMonthReports.has(currentReportName);
}

function hasExplicitDateFilters(queryReport) {
	const routeOptions = frappe.route_options || {};
	const searchParams = new URLSearchParams(window.location.search);

	return Boolean(
		queryReport?.prepared_report_name ||
			routeOptions.from_date ||
			routeOptions.to_date ||
			searchParams.has("prepared_report_name") ||
			searchParams.has("from_date") ||
			searchParams.has("to_date")
	);
}

function applyCurrentMonthDefaults(queryReport) {
	if (
		!isCurrentMonthTechnicianPerformanceReport(queryReport) ||
		hasExplicitDateFilters(queryReport)
	) {
		return;
	}

	queryReport.set_filter_value({
		from_date: frappe.datetime.month_start(),
		to_date: frappe.datetime.month_end(),
	});
}

frappe.query_reports["Technician Performance"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.now_date(), -30),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.now_date(),
			reqd: 1,
		},
		{
			fieldname: "technician",
			label: __("Technician"),
			fieldtype: "Link",
			options: "Technician",
		},
	],

	onload(queryReport) {
		applyCurrentMonthDefaults(queryReport);
	},

	formatter(value, row, column, data, default_formatter) {
		const formatted = default_formatter(value, row, column, data);

		if (!data || column.fieldname !== "completion_rate") {
			return formatted;
		}

		const completionRate = Number(data.completion_rate || 0);
		if (completionRate < 70) {
			return `<span style="color: var(--red-600); font-weight: 600;">${formatted}</span>`;
		}

		if (completionRate >= 90) {
			return `<span style="color: var(--green-600); font-weight: 600;">${formatted}</span>`;
		}

		return formatted;
	},
};
