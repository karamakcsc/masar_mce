# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 220},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 80},
		{"label": _("Target Warehouse"), "fieldname": "target_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 200},
		{"label": _("Transit Warehouse"), "fieldname": "transit_warehouse", "fieldtype": "Data", "width": 200},
		{"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Data", "width": 150},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
		{"label": _("Open Qty"), "fieldname": "open_qty", "fieldtype": "Float", "width": 110},
		{"label": _("No. of Stock Entries"), "fieldname": "no_of_stock_entries", "fieldtype": "Int", "width": 140},
	]


def get_conditions(filters):
	conditions = [
		"se.docstatus = 1",
		"se.purpose = 'Material Transfer'",
		"se.add_to_transit = 1",
		"se.per_transferred < 100",
	]
	values = {}

	if filters.get("company"):
		conditions.append("se.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("from_date"):
		conditions.append("se.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("se.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("item_code"):
		conditions.append("sed.item_code = %(item_code)s")
		values["item_code"] = filters.get("item_code")

	if filters.get("target_warehouse"):
		conditions.append("se.custom_target_location = %(target_warehouse)s")
		values["target_warehouse"] = filters.get("target_warehouse")

	stock_entry = filters.get("stock_entry")
	if stock_entry:
		if isinstance(stock_entry, str):
			stock_entry = frappe.parse_json(stock_entry)
		conditions.append("se.name in %(stock_entry)s")
		values["stock_entry"] = tuple(stock_entry)

	return " and ".join(conditions), values


def get_data(filters):
	conditions, values = get_conditions(filters)

	return frappe.db.sql(
		f"""
		select
			sed.item_code as item_code,
			sed.item_name as item_name,
			sed.uom as uom,
			se.custom_target_location as target_warehouse,
			group_concat(distinct sed.t_warehouse separator ', ') as transit_warehouse,
			group_concat(distinct nullif(ifnull(sed.to_supplier, sed.supplier), '') separator ', ') as supplier,
			max(se.company) as company,
			sum(sed.qty - ifnull(sed.transferred_qty, 0)) as open_qty,
			count(distinct se.name) as no_of_stock_entries
		from `tabStock Entry Detail` sed
		inner join `tabStock Entry` se on se.name = sed.parent
		where {conditions}
		group by sed.item_code, se.custom_target_location, sed.item_name, sed.uom
		having open_qty > 0
		order by sed.item_code, target_warehouse
		""",
		values,
		as_dict=1,
	)
