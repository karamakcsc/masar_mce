import frappe
from frappe import get_all , get_doc , delete_doc
from masar_mce.utils import get_item_barcode, get_tax_for_item, get_item_price
from masar_mce.api import update_pos_item

def after_insert(self, method):
    sync_specific_parties(self)

def on_update(self, method):
    sync_specific_parties(self)
    update_pos_item(self)

def sync_specific_parties(self):
    if not self.item_code:
        return
    current_suppliers = {s.supplier for s in self.supplier_items if s.supplier}
    existing_rows = get_all(
        "Party Specific Item",
        filters={
            "based_on_value": self.item_code,
            "party_type": "Supplier",
            "restrict_based_on": "Item"
        },
        fields=["name", "party"]
    )
    existing_suppliers = {row.party for row in existing_rows}
    to_add = current_suppliers - existing_suppliers
    for supplier in to_add:
        get_doc({
            "doctype": "Party Specific Item",
            "based_on_value": self.item_code,
            "party": supplier,
            "party_type": "Supplier",
            "restrict_based_on": "Item"
        }).insert(ignore_permissions=True)
    to_delete = existing_suppliers - current_suppliers
    for row in existing_rows:
        if row.party in to_delete:
            delete_doc("Party Specific Item", row.name, ignore_permissions=True)
            
            
def update_pos_item(self):
    existing_sp = frappe.db.sql("""
            SELECT tbo.name
            FROM `tabBlanket Order Item` tboi 
            INNER JOIN `tabBlanket Order` tbo ON tboi.parent = tbo.name
            WHERE tboi.item_code = %s AND tbo.docstatus = 1 AND tbo.custom_status = 'Active'
            GROUP BY tbo.name
        """,(self.name,), as_dict=True)
    
    if existing_sp:
        local_zone_tax = get_tax_for_item(self.name, "Local Zone")
        free_zone_tax = get_tax_for_item(self.name, "Free Zone")
        selling_local_zone, selling_free_zone = get_item_price(self.name)
        local_zone = {
            "ITEMNO": self.name,
            "BARCODE": get_item_barcode(self.name),
            "ITEMSHORTNAME": self.name,
            "ITEMTAX": local_zone_tax * 100,
            "ITEMPRICE": selling_local_zone,
            "ITEMSTOP": self.disabled,
            "TRN_TYPE_PRICE": 1
        }
        free_zone = {
            "ITEMNO": self.name,
            "BARCODE": get_item_barcode(self.name),
            "ITEMSHORTNAME": self.name,
            "ITEMTAX": free_zone_tax * 100,
            "ITEMPRICE": selling_free_zone,
            "ITEMSTOP": self.disabled,
            "TRN_TYPE_PRICE": 1
        }
        
        # frappe.throw(f"Local Zone: {local_zone} <br> Free Zone: {free_zone}")
        
        # update_pos_item(local_zone, free_zone)