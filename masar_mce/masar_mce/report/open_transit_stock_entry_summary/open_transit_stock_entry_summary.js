// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Open Transit Stock Entry Summary"] = {
	"filters": [
		{
			"fieldname": "stock_entry",
			"label": __("Stock Entry (Transit)"),
			"fieldtype": "MultiSelectList",
			"get_data": function (txt) {
				return frappe.db.get_link_options("Stock Entry", txt, {
					"purpose": "Material Transfer"
				});
			}
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "target_warehouse",
			"label": __("Target Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse"
		}
	]
};
