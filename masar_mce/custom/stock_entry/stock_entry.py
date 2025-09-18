import frappe 

def on_submit(self , method):
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
            "sample_size": 0
        }).insert(ignore_permissions=True)
        
@frappe.whitelist()
def get_items_from_blanket_order(doctype, txt, searchfield, start, page_len, filters):
    blanket_order = filters.get("blanket_order")
    return frappe.db.sql(f"""
        SELECT DISTINCT item_code as name
        FROM `tabBlanket Order Item`
        WHERE parent = '{blanket_order}'
    """)
    
    
def check_agreement_items(self):
    if self.stock_entry_type != "Material Receipt for Inspection":
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
