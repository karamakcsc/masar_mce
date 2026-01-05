import frappe
from frappe import get_all , get_doc , delete_doc
from masar_mce.utils import get_item_barcode, get_tax_for_item, get_item_price
from masar_mce.api import insert_pos_item

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
    active_sa = None
    if self.custom_latest_sa:
        active_sa = self.custom_latest_sa
    else: 
        existing_sp = frappe.db.sql("""
                SELECT tbo.name
                FROM `tabBlanket Order Item` tboi 
                INNER JOIN `tabBlanket Order` tbo ON tboi.parent = tbo.name
                WHERE tboi.item_code = %s AND tbo.docstatus = 1 AND tbo.custom_status = 'Active'
                GROUP BY tbo.name
            """,(self.name,), as_dict=True)
        if existing_sp:
            active_sa = existing_sp[0].name
      
    if active_sa:
        sa_doc = get_doc("Blanket Order", active_sa)
        supplier_code = frappe.db.get_value("Supplier", sa_doc.supplier, "custom_supplier_code")
        local_zone_tax = get_tax_for_item(self.name, "Local Zone")
        free_zone_tax = get_tax_for_item(self.name, "Free Zone")
        selling_local_zone, selling_free_zone = get_item_price(self.name)
        payload_local_zone = {
            "AGREEMENT_NO": active_sa,
            "COMP_CODE": supplier_code,
            "AGR_STDATE": sa_doc.from_date,
			"AGR_ENDATE": sa_doc.to_date,
            "ITEMS": [
                {
                "ITEMNO": self.name,
                "BARCODE": get_item_barcode(self.name),
                "ITEMSHORTNAME": self.name,
                "ITEMTAX": local_zone_tax * 100,
                "ITEMPRICE": selling_local_zone,
                "ITEMSTOP": self.disabled,
                "TRN_TYPE_PRICE": 1
                }
            ]
        }
        payload_free_zone = {
            "AGREEMENT_NO": active_sa,
            "COMP_CODE": supplier_code,
            "AGR_STDATE": sa_doc.from_date,
            "AGR_ENDATE": sa_doc.to_date,
            "ITEMS": [
                {
                "ITEMNO": self.name,
                "BARCODE": get_item_barcode(self.name),
                "ITEMSHORTNAME": self.name,
                "ITEMTAX": free_zone_tax * 100,
                "ITEMPRICE": selling_free_zone,
                "ITEMSTOP": self.disabled,
                "TRN_TYPE_PRICE": 1
                }
            ]       
        }
        insert_pos_item(payload_local_zone, payload_free_zone)