import frappe 

@frappe.whitelist()
def get_items_by_supplier(doctype, txt, searchfield, start, page_len, filters):
    supplier = filters.get("supplier")
    return frappe.db.sql(f"""
        SELECT DISTINCT parent as name 
        FROM `tabItem Supplier`
        WHERE supplier = '{supplier}'
        ORDER BY parent
    """)
