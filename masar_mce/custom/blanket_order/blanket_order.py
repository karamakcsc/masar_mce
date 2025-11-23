import frappe , json
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
from frappe import _
from datetime import datetime
from masar_mce.utils import get_tax_for_item
def validate(self , method):
    calculate_amounts_and_total(self)
    if self.is_new():
        get_default_penalty(self)
    if self.custom_submit_after_inspection and self.docstatus == 1:
        check_inspection_result(self)
        
def before_update_after_submit(self , method) : 
    if self.custom_status == 'Active': 
        validate_duplicate_item_in_active_blanket_orders(self)
        
def on_submit(self , method): 
    self.db_set('custom_status', 'Active')
    validate_duplicate_item_in_active_blanket_orders(self)
    create_priceing_sheet(self)
def on_cancel(self , method):
    pass
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_by_supplier(doctype, txt, searchfield, start, page_len, filters):
    supplier = filters.get("supplier")
    if not supplier:
        return []
    query = """
        SELECT DISTINCT 
            item_supplier.parent as item_code,
            item.item_name
        FROM `tabItem Supplier` item_supplier
        INNER JOIN `tabItem` item ON item_supplier.parent = item.name
        WHERE item_supplier.supplier = %(supplier)s
        AND item.disabled = 0
        AND (item_supplier.parent LIKE %(txt)s OR item.item_name LIKE %(txt)s)
        ORDER BY item_supplier.parent
        LIMIT %(start)s, %(page_len)s
    """
    return frappe.db.sql(query, {
        'supplier': supplier,
        'txt': f"%{txt}%",
        'start': start,
        'page_len': page_len
    })
def calculate_amounts_and_total(self):
    total , total_qty  = 0  , 0 
    for i in self.items:
        amount = flt(i.qty) * flt(i.rate)
        i.custom_amount = amount
        total += amount
        total_qty += i.qty
        tax_rate = get_tax_for_item(item_code=i.item_code)
        i.custom_purchase_price_after_tax = flt(i.rate) + flt(i.rate) * tax_rate
        i.custom_selling_price_after_tax = flt(i.custom_selling_price) + flt(i.custom_selling_price) * tax_rate
    self.custom_total_quantity = total_qty
    self.custom_agreement_total = total
    
def get_default_penalty(self):
    all_penalty = frappe.db.sql(
        """
        SELECT name, penalty_type, account
        FROM `tabPenalty`
        WHERE `default` = 1
          AND `disabled` = 0
        """,
        as_dict=True,
    )

    for p in all_penalty:
        self.append("custom_penalties", {
            'penalty': p.name,
            'penalty_type': p.penalty_type,
            'account': p.account
        })

@frappe.whitelist()
def create_stock_entry_for_inspection(source_name, target_doc=None, args=None):
    if args is None:
        args = {}
    if isinstance(args, str):
        args = json.loads(args)
    source_doc = frappe.get_doc("Blanket Order", source_name)
    
    inspection_items = [d for d in source_doc.items if d.custom_inspection_is_required]
    if not inspection_items:
        frappe.throw(_("There are no items with 'Inspection is Required' checked."))

    def condition(d):
        return d.custom_inspection_is_required

    doclist = get_mapped_doc(
        "Blanket Order",
        source_name,
        {
            "Blanket Order": {
                "doctype": "Stock Entry",
                "field_map": {
                    "name": "custom_blanket_order",
                    "supplier": "custom_supplier",
                    "transaction_date": "posting_date"
                },
                "validation": {
                    "docstatus": ["=", 0]
                }
            },
            "Blanket Order Item": {
                "doctype": "Stock Entry Detail",
                "field_map": {
                    "item_code": "item_code",
                    "item_name": "item_name",
                    "custom_quality_inspection_quantity": "qty"
                },
                "condition": condition,
                "postprocess": update_item
            },
        },
        target_doc,
        set_missing_values,
    )

    return doclist


def update_item(source_doc, target_doc, source_parent):
    target_doc.qty = source_doc.custom_quality_inspection_quantity or 0


def set_missing_values(source, target):
    target.purpose = "Material Receipt"
    target.stock_entry_type = "سند إستلام لفحص الجودة"
    



def check_inspection_result(self):
    inspection_required_items = [i for i in self.items if i.custom_inspection_is_required]

    if not inspection_required_items:
        frappe.throw(_("No items require inspection in this supplier agreement."))


    for item in inspection_required_items:
        if item.custom_quality_inspection_status != 'Accepted':
            frappe.throw(_("Item {0} has not passed inspection. Please complete the inspection before proceeding.").format(item.item_code))
     
def validate_duplicate_item_in_active_blanket_orders(self):
    current_items = [d.item_code for d in self.items]
    if not current_items:
        return
    duplicates = frappe.db.sql(
        """
        SELECT bo.name AS blanket_order, boi.item_code
        FROM `tabBlanket Order` bo
        INNER JOIN `tabBlanket Order Item` boi ON bo.name = boi.parent
        WHERE bo.docstatus = 1
          AND bo.custom_status = 'Active'
          AND bo.name != %(current_name)s
          AND boi.item_code IN %(items)s
        """,
        {"current_name": self.name or "", "items": tuple(current_items)},
        as_dict=True
    )
    if duplicates:
        msg_lines = [_("The following items are already active in other Blanket Orders:")]
        for d in duplicates:
            msg_lines.append("- {0} in {1}".format(d['item_code'] , d['blanket_order']))
        frappe.throw("<br>".join(msg_lines))
        
def create_priceing_sheet(self):
    rows = list()
    for i in self.items: 
        tax_rate = flt(get_tax_for_item(item_code=i.item_code) )
        rows.append({
            'item_code' : i.item_code , 
            'item_name' : i.item_name , 
            'rate' : i.rate , 
            'markup_percentage' : i.custom_markup_percentage, 
            'selling_price' : i.custom_selling_price,
            'tax_rate' : tax_rate * 100 , 
            'rate_after_tax' :  i.rate + i.rate *tax_rate, 
            'selling_price_after_tax' : flt(i.custom_selling_price) + flt(i.custom_selling_price) * tax_rate 
        })
    frappe.new_doc('Pricing Sheet').update({
        'blanket_order' : self.name , 
        'items' : rows 
    }).save().submit()