import frappe , json
from frappe.utils import flt ,date_diff, add_days
from frappe.model.mapper import get_mapped_doc
from erpnext.buying.doctype.purchase_order.purchase_order import set_missing_values
@frappe.whitelist()
def get_blanket_order_for_item(item_code, supplier):
    if not item_code or not supplier:
        return {}
    result = frappe.db.sql(
        """
        SELECT bo.name AS parent, boi.name AS name , boi.rate as rate
        FROM `tabBlanket Order` bo
        INNER JOIN `tabBlanket Order Item` boi ON bo.name = boi.parent
        WHERE bo.supplier = %(supplier)s
          AND bo.docstatus = 1
          AND bo.custom_status = 'Active'
          AND boi.item_code = %(item_code)s
        LIMIT 1
        """,
        {"supplier": supplier, "item_code": item_code},
        as_dict=True
    )
    return result[0] if result else {}


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_from_active_blanket_order(doctype, txt, searchfield, start, page_len, filters):
    supplier = filters.get("supplier")
    if not supplier:
        return []
    query = """
        SELECT DISTINCT
            boi.item_code,
            item.item_name
        FROM `tabBlanket Order` bo
        INNER JOIN `tabBlanket Order Item` boi ON bo.name = boi.parent
        INNER JOIN `tabItem` item ON boi.item_code = item.name
        WHERE bo.supplier = %(supplier)s
        AND bo.docstatus = 1
        AND bo.custom_status = 'Active'
        AND item.disabled = 0
        AND (boi.item_code LIKE %(txt)s OR item.item_name LIKE %(txt)s)
        ORDER BY boi.item_code
        LIMIT %(start)s, %(page_len)s
    """
    return frappe.db.sql(query, {
        "supplier": supplier,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })


@frappe.whitelist()
def create_purchase_request_from_purchase_order(source_name, target_doc=None, args=None):
    if args is None:
        args = {}
    if isinstance(args, str):
        args = json.loads(args)
    def update_item(obj, target, source_parent):
        target.uom = obj.uom
        target.item_code = obj.item_code
        target.description = obj.description
        target.stock_uom = obj.stock_uom
        target.request_quantity = flt(obj.qty) - flt(obj.received_qty)
        target.purchase_order = obj.parent
        target.purchase_order_item = obj.name
    def select_item(d):
        filtered_items = args.get("filtered_children", [])
        child_filter = d.name in filtered_items if filtered_items else True
        return child_filter

    doc = get_mapped_doc(
        "Purchase Order",
        source_name,
        {
            "Purchase Order": {
                "doctype": "Market Purchase Request",
                "field_map": {
                    "supplier": "supplier", 
                },
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            "Purchase Order Item": {
                "doctype": "Purchase Request Item",
                "field_map": {
                    "name": "purchase_order_item",
                    "parent": "purchase_order",
                },
                "postprocess": update_item,
                "condition": lambda doc: select_item(doc),
            },
        },
        target_doc
    )

    return doc
    
def on_submit(self , method):
    set_agreement_date(self)
    

def set_agreement_date(self):
    agreements = frappe.db.sql("""
        SELECT DISTINCT poi.blanket_order
        FROM `tabPurchase Order Item` poi
        WHERE poi.parent = %s
          AND poi.blanket_order IS NOT NULL
    """, self.name, as_dict=1)

    for agr in agreements:
        if not agr.blanket_order:
            continue

        agr_doc = frappe.get_doc("Blanket Order", agr.blanket_order)

        if not agr_doc.custom_posting_date:
            diff_days = date_diff(self.transaction_date, agr_doc.from_date)

            new_from_date = add_days(agr_doc.from_date, diff_days)
            new_to_date   = add_days(agr_doc.to_date, diff_days)

            frappe.db.set_value("Blanket Order", agr.blanket_order, {
                "custom_posting_date": agr_doc.from_date,
                "from_date": new_from_date,
                "to_date": new_to_date
            })
            
def before_insert(self, method):

    item_codes = [d.item_code for d in self.items]

    prices = frappe.db.sql("""
        SELECT 
            ip.item_code,
            ip.price_list_rate
        FROM `tabItem Price` ip
        INNER JOIN (
            SELECT 
                item_code,
                MAX(valid_from) AS latest_date
            FROM `tabItem Price`
            WHERE buying = 1
              AND item_code IN %(items)s
            GROUP BY item_code
        ) latest
            ON latest.item_code = ip.item_code
           AND latest.latest_date = ip.valid_from
        WHERE ip.buying = 1
    """, {"items": tuple(item_codes)}, as_dict=1)

    price_map = {p.item_code: p.price_list_rate for p in prices}

    for i in self.items:
        i.rate = price_map.get(i.item_code, 0)