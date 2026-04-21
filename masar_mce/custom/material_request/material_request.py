import frappe
from frappe import _

def validate(self , method):
    validate_item_markets_for_material_request(self)
def validate_item_markets_for_material_request(self):
    if not self.items:
        return
    for row in self.items:
        item_code = row.item_code
        warehouse = row.warehouse or self.set_warehouse
        if not warehouse:
            frappe.throw(
                _("Row #{0}: Warehouse is required for item {1}")
                .format(row.idx, item_code)
            )
        has_restriction = frappe.db.exists(
            "Item Markets",
            {
                "item_code": item_code,
                "disabled": 0
            }
        )
        if has_restriction:
            allowed = frappe.db.exists(
                "Item Markets",
                {
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "disabled": 0
                }
            )
            if not allowed:
                frappe.throw(
                    _(
                        "Row #{0}: Item <b>{1}</b> is not allowed in Warehouse <b>{2}</b> as per Item Markets."
                    ).format(row.idx, item_code, warehouse)
                )