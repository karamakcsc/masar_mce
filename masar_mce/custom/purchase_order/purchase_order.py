import frappe

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

    