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
def get_tax_for_item(item_code=None, category='Local Zone'):
    if not item_code or not category:
        return 0
    if not frappe.db.exists('Item', item_code):
        return 0
    item_doc = frappe.get_doc('Item', item_code)
    tax_rate = get_tax_from_taxes(item_doc.taxes, category)
    if tax_rate is not None:
        return tax_rate
    group_doc = frappe.get_doc('Item Group', item_doc.item_group)
    tax_rate = get_tax_from_taxes(group_doc.taxes, category)
    if tax_rate is not None:
        return tax_rate
    return 0
def get_tax_from_taxes(taxes, category):
    """Return tax rate from a taxes table (item or item group)."""
    if not taxes:
        return None
    for tax in taxes:
        if tax.tax_category == category and tax.item_tax_template:
            tax_rate = frappe.db.get_value(
                "Item Tax Template Detail",
                {"parent": tax.item_tax_template},
                "tax_rate"
            )
            return tax_rate / 100 or 0

    return None

def get_standard_price_list_b_s_sfz():
    buying = frappe.db.get_values(
        "Price List",
        {'enabled' : 1 , 'buying' : 1}, 
        "name", as_dict=False
    )
    selling = frappe.db.get_values(
        "Price List",
        {'enabled' : 1 , 'selling' : 1 , 'custom_free_zone' : 0 }, 
        "name", as_dict=False
    )
    selling_free_zone = frappe.db.get_values(
        "Price List",
        {'enabled' : 1 , 'selling' : 1 , 'custom_free_zone' : 1 }, 
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
    if len(selling_free_zone) != 1:
        frappe.throw(_(
            "There must be exactly one enabled Selling Free Zone Price List. "
            "Found {0}".format(len(selling_free_zone))
        ))
    return buying[0][0], selling[0][0], selling_free_zone[0][0]

@frappe.whitelist()
def get_current_stock_value_and_quantity(item_code=None, warehouse=None, cost_zone = 'Local Zone'):
    cond = " w.custom_cost_zone = '{0}' ".format(cost_zone)
    print(f"Getting stock value and quantity for item_code={item_code}, warehouse={warehouse}")
    if item_code in [None , '' , "" , ' ', " "]:
        return {
        'value': 0,
        'quantity': 0
    }
    if item_code:
        cond += f" AND b.item_code = '{item_code}'"
    if warehouse:
        cond += f" AND b.warehouse = '{warehouse}'"

    sql = frappe.db.sql(f"""
        SELECT 
            IFNULL(SUM(stock_value), 0),
            IFNULL(SUM(actual_qty), 0),
            IFNULL(b.valuation_rate  , 0 )
        FROM 
            `tabBin` b
        INNER JOIN 
            `tabWarehouse` w ON b.warehouse = w.name
        WHERE 
            {cond}
    """, as_list=True)

    return {
        'stock_value': sql[0][0],
        'quantity': sql[0][1], 
        'valuation_rate': sql[0][2]
    } if sql else {
        'stock_value': 0,
        'quantity': 0,
        'valuation_rate': 0
    }

def get_item_barcode(item_code):
    if not item_code:
        return None
    barcode = frappe.db.get_value(
        "Item Barcode",
        {"parent": item_code},
        "barcode"
    )
    if barcode:
        return barcode
    return None

def get_item_price(item_code):
    if not item_code:
        return None, None
    buying , selling  , selling_free_zone = get_standard_price_list_b_s_sfz()
    local_zone_rate = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": selling},
        "price_list_rate"
    )
    
    free_zone_rate = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": selling_free_zone},
        "price_list_rate"
    )
    if local_zone_rate and free_zone_rate:
        return local_zone_rate, free_zone_rate
    return None, None