from frappe import get_all , get_doc , delete_doc

def after_insert(self, method):
    sync_specific_parties(self)

def on_update(self, method):
    sync_specific_parties(self)

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
