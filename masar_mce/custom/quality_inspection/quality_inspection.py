from frappe import db , get_doc

def on_submit(self , method):
    update_stock_entry(self)
    
    
def update_stock_entry(self): 
    db.set_value(self.reference_type , self.reference_name  ,'inspection_required' , 1)
    se_doc = get_doc(self.reference_type , self.reference_name)
    for i in se_doc.items:
        if i.item_code == self.item_code:
            db.set_value(i.doctype , i.name , {'quality_inspection' : self.name , 'custom_quality_inspection_status' : self.status} )
            
    update_blanket_order(self , se_doc.custom_supplier_agreement)
    
    
def update_blanket_order(self , sa_name):
    if not sa_name:
        return 
    sa_doc = get_doc('Blanket Order' , sa_name)
    for i in sa_doc.items:
        if i.item_code == self.item_code:
            db.set_value(i.doctype , i.name , {
                'custom_quality_inspection' : self.name , 
                'custom_quality_inspection_status' : self.status , 
                'custom_quality_inspection_remarks' : self.remarks} 
            )
            
            
