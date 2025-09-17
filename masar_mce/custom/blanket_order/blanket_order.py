import frappe 
from frappe import new_doc , db , throw


def on_submit(self, method):
    create_stock_entry(self)
def on_update_after_submit(self , method):
    create_quality_inspection(self)
    
def create_stock_entry(self): 
    se_type = 'Material Transfer for Inspection'
    se_doc = new_doc('Stock Entry')
    se_doc.stock_entry_type = se_type
    se_doc.to_warehouse = get_lab_warehouse()
    se_doc.custom_supplier_agreement = self.name
    for i in self.items: 
        se_doc.append('items' , {
            'item_code' : i.item_code, 
            'qty' : 1
        })    
    se_doc.insert(ignore_permissions=True).submit()

def get_lab_warehouse():
    wh_lab = db.sql(
        "SELECT name FROM `tabWarehouse` WHERE warehouse_type = 'Lab' LIMIT 1",
        as_list=True
    )
    if wh_lab:
        return wh_lab[0][0]
    throw("Warehouse Lab Not Exist")
    
def get_linked_stock_entry(sa_name): 
    return db.sql(f"SELECT name FROM `tabStock Entry` WHERE custom_supplier_agreement = '{sa_name}'")[0][0]

def exist_quality_inspection(se_name , item_code):
    exist_sql = db.sql(f"SELECT name FROM `tabQuality Inspection` WHERE reference_name = '{se_name}' AND item_code = '{item_code}'")
    if exist_sql and exist_sql[0][0]:
        return True
    return False

def create_quality_inspection(self):
    se_name = get_linked_stock_entry(self.name)
    for i in self.items:
        if exist_quality_inspection(se_name , i.item_code): 
            continue
        new_doc("Quality Inspection").update({
            "inspection_type":"Incoming",
            "reference_type":"Stock Entry",
            "reference_name":se_name,
            "item_code":i.item_code,
            "inspected_by" : frappe.session.user,
            "sample_size": 0
        }).insert(ignore_permissions=True)