import frappe 
from erpnext.buying.utils import (
    set_stock_levels,
    validate_item_and_get_basic_data,
    validate_end_of_life,
)
from frappe import _
from frappe.utils import cint, cstr


def validate_for_items(doc) -> None:
	items = []
	for d in doc.get("items"):
		set_stock_levels(row=d)  # update with latest quantities
		item = validate_item_and_get_basic_data(row=d)
		validate_stock_item_warehouse(row=d, item=item)
		validate_end_of_life(d.item_code, item.end_of_life, item.disabled)

		items.append(cstr(d.item_code))

	if (
		items
		and len(items) != len(set(items))
		and not cint(frappe.db.get_single_value("Buying Settings", "allow_multiple_items") or 0)
	):
		frappe.throw(_("Same item cannot be entered multiple times."))
  
def validate_stock_item_warehouse(row, item) -> None:
	if (item.is_stock_item == 1 and row.qty and not row.warehouse 
            and not row.get("delivered_by_supplier")
            and (row.parenttype != "Purchase Order")):
		frappe.throw(
			frappe._("Row #{1}: Warehouse is mandatory for stock Item {0}").format(
				frappe.bold(row.item_code), row.idx
			)
		)
