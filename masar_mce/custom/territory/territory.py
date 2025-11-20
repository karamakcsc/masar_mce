from  frappe import db , get_doc

def on_update(self , method ):
    check_linked_warehouses(self)

def check_linked_warehouses(self): 
    if self.is_group:
        return 
    wh_linked = db.get_all(
        "Warehouse",
        filters={"custom_territory": self.name},
        pluck="name"
    )
    for wh in wh_linked:
        wh_doc = get_doc("Warehouse", wh)
        wh_doc.custom_number_of_days = self.custom_number_of_days
        wh_doc.save()