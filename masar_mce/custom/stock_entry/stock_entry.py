import frappe 

def on_submit(self , method):
    if self.stock_entry_type  in ['Material Receipt for Inspection' , 'سند إستلام لفحص الجودة' ]:
        check_agreement_items(self)
        create_quality_inspection(self)
    
def create_quality_inspection(self):
    exist_items = list()
    for i in self.items:
        if i.item_code in exist_items:
            continue
        exist_items.append(i.item_code)
        frappe.new_doc("Quality Inspection").update({
            "inspection_type":"Incoming",
            "reference_type":"Stock Entry",
            "reference_name":self.name,
            "item_code":i.item_code,
            "inspected_by" : frappe.session.user,
            "sample_size": i.qty
        }).insert(ignore_permissions=True)
        
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_from_blanket_order(doctype, txt, searchfield, start, page_len, filters):
    blanket_order = filters.get("blanket_order")
    if not blanket_order:
        return []

    query = """
        SELECT DISTINCT 
            boi.item_code AS name,
            item.item_name
        FROM `tabBlanket Order Item` boi
        INNER JOIN `tabItem` item ON boi.item_code = item.name
        WHERE boi.parent = %(blanket_order)s
        AND (boi.item_code LIKE %(txt)s OR item.item_name LIKE %(txt)s)
        ORDER BY boi.item_code
        LIMIT %(start)s, %(page_len)s
    """

    return frappe.db.sql(query, {
        "blanket_order": blanket_order,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })

    
    
def check_agreement_items(self):
    if self.stock_entry_type not in ['Material Receipt for Inspection' , 'سند إستلام لفحص الجودة' ]:
        return

    if not self.custom_supplier_agreement:
        frappe.throw("Please select a Blanket Order in Custom Supplier Agreement.")

    allowed_items = frappe.get_all(
        "Blanket Order Item",
        filters={"parent": self.custom_supplier_agreement},
        pluck="item_code"
    )

    for row in self.items:
        if row.item_code not in allowed_items:
            frappe.throw(
                f"Item {row.item_code} is not in Blanket Order {self.custom_supplier_agreement}"
            )
