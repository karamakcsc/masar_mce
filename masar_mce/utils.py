import frappe 
from datetime import datetime
from frappe import _
def check_expierd_supplier_agrrement():
    date = datetime.now().date()
    active_sa = frappe.db.sql(
        f"""
        SELECT name FROM `tabBlanket Order` tbo 
        WHERE to_date < '{date}'
        AND tbo.docstatus =1 
        AND tbo.custom_status = 'Active'
        """ , as_dict = True
    )
    for sa in active_sa:
        sa_doc = frappe.get_doc('Blanket Order', sa.name)
        sa_doc.custom_status = 'Expired'
        sa_doc.save()
@frappe.whitelist()
def get_tax_for_item(item_code = None ):
    if not item_code:
        return 0
    item_doc = frappe.get_doc("Item", item_code)
    def get_rate_from_template(template_name):
        if not template_name:
            return 0
        if not frappe.db.exists("Item Tax Template", template_name):
            return 0
        tax_rate = frappe.db.get_value(
            "Item Tax Template Detail",
            {"parent": template_name},
            "tax_rate"
        )
        return tax_rate/100 or 0
    if item_doc.taxes:
        item_template = item_doc.taxes[0].get("item_tax_template")
        rate = get_rate_from_template(item_template)
        if rate:
            return rate
    group_doc = frappe.get_doc("Item Group", item_doc.item_group)
    if group_doc.taxes:
        group_template = group_doc.taxes[0].get("item_tax_template")
        rate = get_rate_from_template(group_template)
        if rate:
            return rate
    return 0

def get_standard_price_list_buying_then_selling():
    buying = frappe.db.get_values(
        "Price List",
        {'enabled' : 1 , 'buying' : 1}, 
        "name", as_dict=False
    )
    selling = frappe.db.get_values(
        "Price List",
        {'enabled' : 1 , 'selling' : 1}, 
        "name", as_dict=False
    )
    if len(buying) != 1: 
        frappe.throw(_(
            "There must be exactly one enabled Buying Price List. "
            "Found {0}".format(len(buying))
        ))
    if len(selling) != 1:
        frappe.throw(_(
            "There must be exactly one enabled Selling Price List. "
            "Found {0}".format(len(selling))
        ))
    return buying[0][0], selling[0][0]
    