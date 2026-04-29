import frappe , json
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
from frappe import _
from datetime import datetime
from masar_mce.utils import get_tax_for_item, get_item_barcode
from masar_mce.api import insert_pos_item
def validate(self , method):
    set_none_posting_date(self)
    calculate_amounts_and_total(self)
    if self.is_new():
        get_default_penalty(self)
    # validate_some_markets_checkbox(self)
    # validate_some_markets(self)
    if self.custom_submit_after_inspection and self.docstatus == 1:
        check_inspection_result(self)
        
def on_update(self, method):
    if self.docstatus == 0:
        sync_pricing_sheet_from_agreement(self, submit_if_needed=False)

def before_update_after_submit(self, method):
    sync_pricing_sheet_from_agreement(self, submit_if_needed=False)
    if self.custom_status == "Active":
        validate_duplicate_item_in_active_blanket_orders(self)

def on_submit(self, method):
    self.db_set("custom_status", "Active")
    validate_duplicate_item_in_active_blanket_orders(self)
    sync_pricing_sheet_from_agreement(self, submit_if_needed=True)
    set_receipt_allowance_for_items(self)

    insert_latest_sa_in_item(self)
def on_cancel(self , method):
    delinked_qualitiy_inspection(self)
def set_none_posting_date(self):
    if self.docstatus == 0 :
        self.custom_posting_date = None
        frappe.db.set_value(self.doctype , self.name , "custom_posting_date" , None , update_modified = False)
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
        
def sync_pricing_sheet_from_agreement(blanket_order_doc, submit_if_needed=False):
    ps_name = frappe.db.get_value(
        "Pricing Sheet",
        filters={
            "blanket_order": blanket_order_doc.name,
            "from_agreement": 1,
        },
        fieldname="name",
        order_by="modified desc",
    )

    if ps_name:
        ps = frappe.get_doc("Pricing Sheet", ps_name)
    else:
        ps = frappe.new_doc("Pricing Sheet")
        ps.from_agreement = 1
        ps.blanket_order = blanket_order_doc.name

    ps.supplier = blanket_order_doc.supplier
    ps.supplier_name = blanket_order_doc.supplier_name
    ps.company = blanket_order_doc.company
    ps.posting_date = blanket_order_doc.from_date or frappe.utils.nowdate()
    ps.pricing_type = blanket_order_doc.custom_pricing_type or "Buying Price Basis"

    ps.set("items", [])

    for i in (blanket_order_doc.items or []):
        free_tax_rate = get_tax_for_item(i.item_code, "Free Zone")
        local_tax_rate = get_tax_for_item(i.item_code, "Local Zone")
        markup_percentage = flt(i.custom_markup_percentage or 0)
        selling_price = flt(i.custom_selling_price or 0)
        purchase_price = flt(i.rate or 0)

        row = {
            "item_code": i.item_code,
            "item_name": i.item_name,
            "new_purchase_price": purchase_price,
            "new_quantity": i.qty,
            "local_tax_rate": flt(local_tax_rate) * 100,
            "free_tax_rate": flt(free_tax_rate) * 100,
            "local_mp": markup_percentage,
            "free_mp": markup_percentage,
            "blanket_order_item": i.name,
        }

        if ps.pricing_type == "Selling Price Basis":
            row["local_sp"] = selling_price

        ps.append("items", row)

    frappe.flags.in_agreement_sync = True
    try:
        if ps.docstatus == 1:
            return ps.name
        ps.save(ignore_permissions=True)

        if submit_if_needed and blanket_order_doc.docstatus == 1 and ps.docstatus == 0:
            ps.submit()

    finally:
        frappe.flags.in_agreement_sync = False

    return ps.name

def insert_latest_sa_in_item(self):
    for item in self.items:
        frappe.db.set_value("Item", item.item_code, "custom_latest_sa", self.name)
        
def set_receipt_allowance_for_items(self):
    if not self.custom_receipt_allowance_check and self.custom_receipt_allowance == 0 :
        return
    item_codes =  [d.item_code for d in self.items]
    placeholders = ", ".join(["%s"] * len(item_codes)) 
    query = f"""
    UPDATE `tabItem`
    SET over_delivery_receipt_allowance = %s
    WHERE item_code IN ({placeholders})
    """
    params = [self.custom_receipt_allowance] + item_codes
    frappe.db.sql(query, params)
def delinked_qualitiy_inspection(self):
    linked_inspections = frappe.db.sql("""
                                SELECT name FROM `tabQuality Inspection`
                                WHERE docstatus =1 and custom_supplier_agreement = %s""",
                                self.name, as_dict=True)
    for inspection in linked_inspections:
        in_doc = frappe.get_doc("Quality Inspection", inspection.name)
        in_doc.cancel()
        in_doc.db_set("custom_supplier_agreement", None)
        frappe.db.commit()
        
# def validate_some_markets(self):
#     for item in self.items:
#         custom_markets = frappe.db.get_all(
#             "Item Markets",
#             filters={"parent": item.item_code, "parentfield": "custom_markets"},
#             fields=["warehouse"]
#         )
#         if item.custom_some_markets:
#             if not custom_markets:
#                 frappe.throw(
#                     _("Item {0} is marked as 'Some Markets' but has no markets specified in its master record.")
#                     .format(item.item_code)
#                 )
#         else:
#             if custom_markets:
#                 frappe.throw(
#                     _("Item {0} is not marked as 'Some Markets' but has markets specified in its master record. "
#                       "Please either check 'Some Markets' or clear the markets in the item master.")
#                     .format(item.item_code)
#                 )
# def validate_some_markets_checkbox(self):
#     if self.custom_some_markets:
#         has_some_markets = any(item.custom_some_markets for item in self.items)
        
#         if not has_some_markets:
#             frappe.throw(
#                 _("At least one item must be marked as 'Some Markets' when 'Some Markets' is checked.")
#             )