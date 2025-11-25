import frappe 
def validate(self , method): 
    if self.custom_special_terms and self.custom_other_terms:
        frappe.throw(frappe._("Cannot have both Custom Special Terms and Custom Other Terms filled."))