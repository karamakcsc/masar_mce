def custom_purchase_order_dashboard(data=None):
    lists = data["transactions"][0]['items']
    lists.append('Purchase Request')
    return data