// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Role Permissions Per Doctype"] = {
	"filters": [
		{
			"fieldname": "doctype",
			"label": "DocType",
			"fieldtype": "Link",
			"options": "DocType"
		},
		{
			"fieldname":"role",
			"label":"Role",
			"fieldtype": "Link",
			"options": "Role"
		},
	]
};
