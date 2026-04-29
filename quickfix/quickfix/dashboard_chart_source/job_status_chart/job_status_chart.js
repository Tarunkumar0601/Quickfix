frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Job Status Chart"] = {
	method: "quickfix.dashboard.get_status_chart_data",
	filters: [],
};
