def custom_blanket_order_dashboard(data=None):
    data.setdefault("non_standard_fieldnames", {})
    data["non_standard_fieldnames"]["Stock Entry"] = "custom_supplier_agreement"
    new_transactions = []
    for t in data.get("transactions", []):
        items = [i for i in t.get("items", []) if i == "Purchase Order"]
        if items:
            if "Pricing Sheet" not in items:
                items.append("Pricing Sheet")
            if "Stock Entry" not in items:
                items.append("Stock Entry")
            t["items"] = items
            new_transactions.append(t)
    data["transactions"] = new_transactions
    return data