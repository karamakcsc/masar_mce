import frappe 

def after_insert(self, method):
    self.custom_supplier_code = self.name 
    frappe.db.set_value("Supplier", self.name, "custom_supplier_code", self.custom_supplier_code , update_modified=False)