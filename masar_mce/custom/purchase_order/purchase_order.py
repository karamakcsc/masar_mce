import frappe

@frappe.whitelist()
def get_rate_and_name_blanket_order_item(parent , item_code):
    if not parent  or not item_code : 
        return False
    result = frappe.db.sql(f"""
            SELECT name , parent , rate 
            FROM `tabBlanket Order Item`
            WHERE parent = '{parent}'
            AND item_code = '{item_code}'
    """ , as_dict=True)
    if result: 
        return result[0]
    return False

@frappe.whitelist()
def get_all_items_from_supplier_agreement(supplier_agreement):
    if supplier_agreement is None : 
        return 
    return  frappe.db.sql(f"""
               SELECT
                    item_code , 
                    qty , 
                    rate 
                FROM `tabBlanket Order Item`
                WHERE parent = '{supplier_agreement}'
                         """ , as_dict=True)