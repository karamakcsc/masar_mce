import frappe , json
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
from frappe import _
from datetime import datetime
from masar_mce.utils import get_tax_for_item, get_item_barcode
from masar_mce.api import insert_pos_item
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
    create_pricing_sheet(self)
    create_pos_item(self)
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
        
def create_pricing_sheet(self):
    rows = list()
    for i in self.items: 
        free_tax_rate = get_tax_for_item(i.item_code, 'Free Zone')
        local_tax_rate = get_tax_for_item(i.item_code, 'Local Zone')
        markup_percentage = flt(i.custom_markup_percentage or 0)
        selling_after_tax = flt(i.custom_selling_price_after_tax or 0)
        purchase_price = flt(i.rate or 0)
        if self.custom_pricing_type == "Buying Price Basis":
            local_pp_after_tax = purchase_price * (1 + local_tax_rate)
            free_pp_after_tax = purchase_price * (1 + free_tax_rate)
            local_sp_after_tax = local_pp_after_tax * (1 + markup_percentage / 100)
            free_sp_after_tax = free_pp_after_tax * (1 + markup_percentage / 100)
            local_sp = local_sp_after_tax / (1 + local_tax_rate)
            free_sp = free_sp_after_tax / (1 + free_tax_rate)
            
        elif self.custom_pricing_type == "Selling Price Basis":
            if selling_after_tax:
                local_sp_after_tax = selling_after_tax
                free_sp_after_tax = selling_after_tax
                local_sp = local_sp_after_tax / (1 + local_tax_rate)
                free_sp = free_sp_after_tax / (1 + free_tax_rate)
                if markup_percentage and markup_percentage != -100:
                    local_pp_after_tax = local_sp_after_tax / (1 + markup_percentage / 100)
                    free_pp_after_tax = free_sp_after_tax / (1 + markup_percentage / 100)
                    purchase_price = local_pp_after_tax / (1 + local_tax_rate)
                elif markup_percentage == -100:
                    local_pp_after_tax = 0
                    free_pp_after_tax = 0
                    purchase_price = 0
                else:
                    local_pp_after_tax = local_sp_after_tax
                    free_pp_after_tax = free_sp_after_tax
                    purchase_price = local_sp_after_tax / (1 + local_tax_rate)
            else:
                local_pp_after_tax = purchase_price * (1 + local_tax_rate)
                free_pp_after_tax = purchase_price * (1 + free_tax_rate)
                local_sp_after_tax = local_pp_after_tax * (1 + markup_percentage / 100)
                free_sp_after_tax = free_pp_after_tax * (1 + markup_percentage / 100)
                local_sp = local_sp_after_tax / (1 + local_tax_rate)
                free_sp = free_sp_after_tax / (1 + free_tax_rate)
        else:
            local_pp_after_tax = purchase_price * (1 + local_tax_rate)
            free_pp_after_tax = purchase_price * (1 + free_tax_rate)
            local_sp_after_tax = local_pp_after_tax * (1 + markup_percentage / 100)
            free_sp_after_tax = free_pp_after_tax * (1 + markup_percentage / 100)
            local_sp = local_sp_after_tax / (1 + local_tax_rate)
            free_sp = free_sp_after_tax / (1 + free_tax_rate)
        rows.append({
            'item_code': i.item_code, 
            'item_name': i.item_name, 
            'new_purchase_price': purchase_price, 
            'new_quantity': i.qty,
            'local_sp': local_sp,
            'free_sp': free_sp, 
            'local_tax_rate': local_tax_rate * 100,
            'free_tax_rate': free_tax_rate * 100,  
            'local_pp_after_tax': local_pp_after_tax,
            'free_pp_after_tax': free_pp_after_tax,
            'local_mp': markup_percentage,
            'free_mp': markup_percentage, 
            'local_sp_after_tax': local_sp_after_tax,
            'free_sp_after_tax': free_sp_after_tax,  
            'blanket_order_item': i.name 
        })
    pricing_sheet = frappe.new_doc('Pricing Sheet')
    pricing_sheet.update({
        'blanket_order': self.name,
        'supplier': self.supplier,
        'supplier_name': self.supplier_name,
        'company': self.company,
        'posting_date': self.from_date or frappe.utils.nowdate(),
        'pricing_type': self.custom_pricing_type or "Buying Price Basis"  # Use same pricing type
    })
    for row in rows:
        pricing_sheet.append('items', row)
    pricing_sheet.save()
    pricing_sheet.calculate_pricing_after_tax_and_there_totals()
    pricing_sheet.submit()
    frappe.msgprint(f"Pricing Sheet {pricing_sheet.name} created successfully." , alert=1)
    return pricing_sheet.name
    
###### MK ######   
def create_pos_item(self):
    if self.docstatus == 1 and self.custom_status == "Active":
        items_local_zone = []
        items_free_zone = []
        supplier_code = frappe.db.get_value("Supplier", self.supplier, "custom_supplier_code")
        for item in self.items:
            is_disabled = frappe.db.get_value("Item", item.item_code, "disabled")
            local_zone_tax = get_tax_for_item(item.item_code, "Local Zone")
            free_zone_tax = get_tax_for_item(item.item_code, "Free Zone")
            items_local_zone.append({
                "ITEMNO": item.item_code,
                "BARCODE": get_item_barcode(item.item_code),
                "ITEMSHORTNAME": item.item_name,
                "ITEMTAX": local_zone_tax * 100,
                "ITEMPRICE": item.custom_selling_price_after_tax,
                "ITEMSTOP": is_disabled,
                "TRN_TYPE_PRICE": 1
            })
            items_free_zone.append({
                "ITEMNO": item.item_code,
                "BARCODE": get_item_barcode(item.item_code),
                "ITEMSHORTNAME": item.item_name,
                "ITEMTAX": free_zone_tax * 100,
                "ITEMPRICE": item.custom_selling_price,
                "ITEMSTOP": is_disabled,
                "TRN_TYPE_PRICE": 1
            })
            
        payload_local_zone = {
            "AGREEMENT_NO": self.name,
            "ITEMS": items_local_zone,
            "COMP_CODE": supplier_code if supplier_code else "",
            "AGR_STDATE": self.from_date,
            "AGR_ENDATE": self.to_date,
        }
        payload_free_zone = {
            "AGREEMENT_NO": self.name,
            "ITEMS": items_free_zone,
            "COMP_CODE": supplier_code if supplier_code else "",
            "AGR_STDATE": self.from_date,
            "AGR_ENDATE": self.to_date,
        }
        
        # frappe.throw(f"Local Zone: {payload_local_zone} <br> Free Zone: {payload_free_zone}")
        
        # insert_pos_item(payload_local_zone, payload_free_zone)
        
        