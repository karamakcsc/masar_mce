def custom_purchase_receipt_dashboard(data=None):
    data = data or {}
    data.setdefault("non_standard_fieldnames", {})
    data["non_standard_fieldnames"]["Material Inspection"] = "purchase_receipt"
    found = False
    for transaction in data.get("transactions", []):
        if "items" in transaction:
            if "Material Inspection" not in transaction["items"]:
                transaction["items"].append("Material Inspection")
            found = True
            break
    if not found:
        data["transactions"] = [
            {
                "label": "Reference",
                "items": ["Material Inspection"]
            }
        ]
    return data