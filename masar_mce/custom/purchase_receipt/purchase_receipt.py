import frappe 
from frappe.utils import getdate , flt

def on_submit(self , method): 
    create_auto_penalty_entry(self)
    check_rquest_to_accepted_qty(self)
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_from_open_purchase_orders(doctype, txt, searchfield, start, page_len, filters):
    supplier = filters.get("supplier")
    if not supplier:
        return []
    query = """
        SELECT
            poi.item_code,
            po.name AS purchase_order,
            poi.name AS purchase_order_item,
            poi.qty - IFNULL(poi.received_qty, 0) + poi.qty * IFNULL(item.over_delivery_receipt_allowance , 0) AS available_qty
        FROM `tabPurchase Order` po
        INNER JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
        INNER JOIN `tabItem` item ON poi.item_code = item.name
        WHERE po.supplier = %(supplier)s
          AND po.docstatus = 1
          AND po.status NOT IN ('Closed', 'Hold')
          AND item.disabled = 0
          AND (poi.item_code LIKE %(txt)s OR item.item_name LIKE %(txt)s)
        HAVING available_qty > 0
        ORDER BY poi.item_code , po.transaction_date
        LIMIT %(start)s, %(page_len)s
    """
    result = frappe.db.sql(query, {
        "supplier": supplier,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    }, as_dict=True)
    return [
        (
            row.item_code,
            f"Qty:{row.available_qty} ",
            row.purchase_order
        )
        for row in result
    ]

@frappe.whitelist()
def get_po_details_for_item(item_code, supplier, used_pos=None):
    if used_pos is None:
        used_pos = []
    if isinstance(used_pos, str):
        import json
        try:
            used_pos = json.loads(used_pos)
        except:
            used_pos = []
    query = f"""
        SELECT
            po.name AS purchase_order,
            poi.name AS purchase_order_item, 
            10 AS rate
        FROM `tabPurchase Order` po
        INNER JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
        INNER JOIN `tabItem` item ON poi.item_code = item.name
        WHERE po.supplier = '{supplier}'
          AND po.docstatus = 1
          AND po.status NOT IN ('Closed', 'Hold')
          AND poi.item_code = '{item_code}'
          AND (poi.qty - IFNULL(poi.received_qty,0) + poi.qty * IFNULL(item.over_delivery_receipt_allowance,0)) > 0
    """
    if used_pos:
        pos_not_in = ", ".join([f"'{p}'" for p in used_pos])
        query += f" AND po.name NOT IN ({pos_not_in})"
    query += " ORDER BY po.transaction_date, po.name LIMIT 1"

    result = frappe.db.sql(query, {
        "supplier": supplier,
        "item_code": item_code,
        "used_pos": tuple(used_pos) if used_pos else ()
    }, as_dict=True)
    return result[0] if result else {}

def create_auto_penalty_entry(self): 
    posting_date = getdate(self.posting_date)
    delivery_date = getdate(self.custom_delivery_date)
    if posting_date > delivery_date:
        penalties = frappe.db.sql("""
            SELECT name as penalty, penalty_type , account , penalty_percentage
            FROM `tabPenalty`
            WHERE disabled = 0 
            AND based_on_days = 1 
            AND auto = 1
        """  , as_dict = True)
        if penalties:
            entry = {
                'supplier' : self.supplier, 
                'purchase_receipt' : self.name , 
                'posting_date' : self.posting_date,
                'penalties' : penalties
            }
            frappe.new_doc('Penalty Entry').update(entry).insert(ignore_permissions = True).submit()

def check_rquest_to_accepted_qty(self): 
    for i in self.items: 
        if flt(i.qty) + flt(i.rejected_qty) > flt(i.custom_request_quantity):
            frappe.throw(
                """The total of Accepted Qty ({0}) and Rejected Qty ({1}) "
                cannot exceed the Requested Quantity ({2}) for item {3}.
                """.format(flt(i.qty) ,flt(i.rejected_qty) , flt(i.custom_request_quantity) , i.item_code)
            )

        