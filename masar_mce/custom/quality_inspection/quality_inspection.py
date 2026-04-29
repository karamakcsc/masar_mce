from frappe import db , get_doc , msgprint
import frappe 

def on_submit(self , method):
    update_stock_entry(self)
    qi_on_submit(self)
def on_cancel(self , method):
    delinked_supplier_agreement(self)
def update_stock_entry(self): 
    db.set_value(self.reference_type , self.reference_name  ,'inspection_required' , 1)
    se_doc = get_doc(self.reference_type , self.reference_name)
    for i in se_doc.items:
        if i.item_code == self.item_code:
            db.set_value(i.doctype , i.name , {'quality_inspection' : self.name , 'custom_quality_inspection_status' : self.status , 'custom_quality_inspection_quantity' : self.sample_size} )
            
    update_blanket_order(self , se_doc.custom_supplier_agreement)
    
    
def update_blanket_order(self , sa_name):
    if not sa_name:
        return 
    sa_doc = get_doc('Blanket Order' , sa_name)
    for i in sa_doc.items:
        if i.item_code == self.item_code:
            if sa_doc.docstatus:
                db.set_value(i.doctype , i.name , {
                    'custom_quality_inspection' : self.name , 
                    'custom_quality_inspection_status' : self.status , 
                    'custom_quality_inspection_remarks' : self.remarks , 
                    'custom_quality_inspection_quantity' : self.sample_size,
                    'custom_inspection_is_required' : 1} 
                )
            else: 
                i.custom_quality_inspection = self.name
                i.custom_quality_inspection_status =  self.status 
                i.custom_quality_inspection_remarks =  self.remarks
                i.custom_quality_inspection_quantity = self.sample_size
                i.custom_inspection_is_required = 1
                sa_doc.save()
                

def qi_on_submit(self):
    if self.reference_type != "Stock Entry":
        return

    se = get_doc("Stock Entry", self.reference_name)
    if se.stock_entry_type in ['Material Receipt for Inspection' , 'سند إستلام لفحص الجودة' ]:
        for item in se.items:
            exists = db.exists(
                "Quality Inspection",
                {
                    "reference_type": "Stock Entry",
                    "reference_name": se.name,
                    "item_code": item.item_code,
                    "docstatus": 1, 
                },
            )
            if not exists:
                return
        notification_doc = frappe.new_doc("Notification Log")
        notification_doc.subject = f"Inspection Result for {se.custom_supplier_agreement}"
        notification_doc.email_content = f"""
        All Quality Inspections for Stock Entry {se.name} are complete.
        Quality testing for Stock Entry {se.name} is finalized. Results approved/rejected.
        """
        notification_doc.type = 'Alert'
        notification_doc.document_type = self.doctype
        notification_doc.document_name = self.name
        notification_doc.from_user = frappe.session.user
        notification_doc.for_user = frappe.session.user
        notification_doc.insert(ignore_permissions=True)
       
     
@frappe.whitelist()
def make_penalty_entry(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def set_missing_values(source, target):
        supplier = None
        supplier_name = None
        if source.reference_type == "Stock Entry" and source.reference_name:
            supplier = frappe.db.get_value(
                "Stock Entry",
                source.reference_name,
                "custom_supplier"
            )
            if supplier:
                supplier_name = frappe.db.get_value(
                    "Supplier",
                    supplier, 
                    "supplier_name"
                )
        target.supplier = supplier
        target.supplier_name = supplier_name
        target.reference_type = "Quality Inspection"
        target.quality_inspection = source.name
        target.reference_name = source.reference_name 
    doc = get_mapped_doc(
        "Quality Inspection",
        source_name,
        {
            "Quality Inspection": {
                "doctype": "Penalty Entry",
            }
        },
        target_doc,
        set_missing_values
    )
    return doc

def delinked_supplier_agreement(self):
    if self.custom_supplier_agreement is None:
        return
    sa_doc = get_doc('Blanket Order' , self.custom_supplier_agreement)
    for i in sa_doc.items:
        if i.custom_quality_inspection == self.name:
            db.set_value(i.doctype , i.name , {
                'custom_quality_inspection' : None , 
                'custom_quality_inspection_status' : None , 
                'custom_quality_inspection_remarks' : None , 
                'custom_quality_inspection_quantity' : None,
                'custom_inspection_is_required' : 0} 
            )
    db.set_value(self.doctype , self.name , 'custom_supplier_agreement' , None)
    frappe.db.commit()