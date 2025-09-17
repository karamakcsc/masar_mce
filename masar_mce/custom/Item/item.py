

import frappe

def after_insert(self, method):
    if self.custom_supplier:
        create_specific_party(self)

def on_update(self, method):
    if self.custom_supplier:
        update_specific_party(self)

def create_specific_party(self):
    if frappe.db.exists("Item", self.item_code):
        specific_party = frappe.get_doc({
            "doctype": "Party Specific Item",
            "based_on_value": self.item_code,
            "party": self.custom_supplier,
            "party_type": "Supplier",
            "restrict_based_on": "Item"
        })
        specific_party.insert(ignore_permissions=True)

def update_specific_party(self):
    existing = frappe.db.exists("Party Specific Item", {
        "based_on_value": self.item_code,
        "party_type": "Supplier",
        "restrict_based_on": "Item"
    })
    
    if existing:
        specific_party = frappe.get_doc("Party Specific Item", existing)
        specific_party.party = self.custom_supplier
        specific_party.save(ignore_permissions=True)
    else:
        create_specific_party(self)