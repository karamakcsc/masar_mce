def custom_blanket_order_dashboard(data=None):
    new_transactions = []
    for t in data.get("transactions", []):
        if "items" in t:
            t["items"] = [i for i in t["items"] if i == "Purchase Order"]
            if t["items"]:
                new_transactions.append(t)
    lists = data["transactions"][0]['items']
    lists.append('Pricing Sheet')
    data["transactions"] = new_transactions
    return data
