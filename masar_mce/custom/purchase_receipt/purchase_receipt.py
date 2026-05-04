import frappe 
import json
from frappe import _
from frappe.utils import flt, get_link_to_form, getdate , date_diff
from erpnext.controllers.status_updater import StatusUpdater
from masar_mce.utils import get_inspection_status
from frappe.model.mapper import get_mapped_doc

check_overflow_with_allowance = StatusUpdater.check_overflow_with_allowance
limits_crossed_error = StatusUpdater.limits_crossed_error
def validate(self , method ):
    validate_qty(self)
    validate_inspection_status(self)
    validate_some_markets_warehouse(self)
def on_cancel(self , method):
    update_received_qty_on_cancel(self)  
def on_submit(self , method):
    if self.is_return == 0 :
        create_auto_penalty_entry(self)
        check_request_to_accepted_qty(self)
    update_received_qty(self)
def before_insert(self , method):
    set_purchase_order_rate(self)
    set_selling_price_list(self)
def set_selling_price_list(self):
    if self.is_return == 0 :
        return
    for item in self.items:
        cost_zone = frappe.db.get_value('Warehouse', item.warehouse, 'custom_cost_zone')
        SQL = f"""
                SELECT 
                    ROUND(IFNULL(ip.price_list_rate , 0 ) , 3)
                FROM 
                    `tabItem Price` ip
                WHERE 
                    ip.item_code = '{item.item_code}'
                    AND ip.selling = 1
                    AND ip.custom_free_zone = {'1' if cost_zone == 'Free Zone' else '0'}
                    AND ip.valid_from = (
                        SELECT 
                            MAX(valid_from)
                        FROM 
                            `tabItem Price`
                        WHERE 
                            item_code = '{item.item_code}'
            )
        """
        price_list_rate = frappe.db.sql(SQL , as_list = 1)
        if price_list_rate and price_list_rate[0][0]:
            item.rate = flt(price_list_rate[0][0])
        
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_from_open_purchase_orders(doctype, txt, searchfield, start, page_len, filters):
    supplier = filters.get("supplier")
    warehouse = filters.get("warehouse")
    query = """
        SELECT
            poi.item_code,
            poi.item_name,
            po.name AS purchase_order,
            poi.name AS purchase_order_item,
            poi.qty - IFNULL(poi.received_qty, 0) 
                + poi.qty * IFNULL(item.over_delivery_receipt_allowance, 0) AS available_qty
        FROM `tabPurchase Order` po
        INNER JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
        INNER JOIN `tabItem` item ON poi.item_code = item.name
        WHERE po.supplier = %(supplier)s
          AND po.docstatus = 1
          AND po.status NOT IN ('Closed', 'Hold')
          AND item.disabled = 0
          AND (poi.item_code LIKE %(txt)s OR item.item_name LIKE %(txt)s)
          AND (
                NOT EXISTS (
                    SELECT 1 
                    FROM `tabItem Markets` im2
                    WHERE im2.item_code = poi.item_code
                      AND im2.disabled = 0
                )
                OR EXISTS (
                    SELECT 1 
                    FROM `tabItem Markets` im3
                    WHERE im3.item_code = poi.item_code
                      AND im3.disabled = 0
                      AND im3.warehouse = %(warehouse)s
                )
          )

        HAVING available_qty > 0
        ORDER BY poi.item_code, po.transaction_date
        LIMIT %(start)s, %(page_len)s
    """

    result = frappe.db.sql(query, {
        "supplier": supplier,
        "warehouse": warehouse,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    }, as_dict=True)

    return [
        (
            row.item_code,
            f"<b>Name:</b> {row.item_name}, "
            f"<b>PO:</b> {row.purchase_order}, "
            f"<b>Qty:</b> {frappe.utils.fmt_money(row.available_qty, currency=None)}<br>"
        )
        for row in result
    ]

@frappe.whitelist()
def get_po_details_for_item(item_code, supplier, used_pos=None):
    if used_pos is None:
        used_pos = []
    if isinstance(used_pos, str):
        import json
        try:
            used_pos = json.loads(used_pos)
        except:
            used_pos = []
    query = f"""
        SELECT
            po.name AS purchase_order,
            poi.name AS purchase_order_item, 
            poi.rate AS rate
        FROM `tabPurchase Order` po
        INNER JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
        INNER JOIN `tabItem` item ON poi.item_code = item.name
        WHERE po.supplier = '{supplier}'
          AND po.docstatus = 1
          AND po.status NOT IN ('Closed', 'Hold')
          AND poi.item_code = '{item_code}'
          AND (poi.qty - IFNULL(poi.received_qty,0) + poi.qty * IFNULL(item.over_delivery_receipt_allowance,0)) > 0
    """
    if used_pos:
        pos_not_in = ", ".join([f"'{p}'" for p in used_pos])
        query += f" AND po.name NOT IN ({pos_not_in})"
    query += " ORDER BY po.transaction_date, po.name LIMIT 1"

    result = frappe.db.sql(query, {
        "supplier": supplier,
        "item_code": item_code,
        "used_pos": tuple(used_pos) if used_pos else ()
    }, as_dict=True)
    return result[0] if result else {}

def create_auto_penalty_entry(self): 
    posting_date = getdate(self.posting_date)
    request_date = getdate(self.custom_request_date)
    diff_days = date_diff(posting_date, request_date)
    if not self.set_warehouse:
        frappe.throw(_("Please set 'Accepted Warehouse' before submitting the Purchase Receipt."))
    if not self.supplier:
        frappe.throw(_("Please set 'Supplier' before submitting the Purchase Receipt."))
    territory = frappe.db.get_value("Warehouse", self.set_warehouse, "custom_territory")
    allowed_days = 0
    if territory:
        supplier_doc = frappe.get_doc("Supplier", self.supplier)
        for row in supplier_doc.custom_territories:
            if row.territory == territory:
                allowed_days = row.number_of_days or 0
                break
    if diff_days > allowed_days:
        penalties = frappe.db.sql("""
            SELECT name as penalty, penalty_type , account , penalty_percentage
            FROM `tabPenalty`
            WHERE disabled = 0 
            AND based_on_days = 1 
            AND auto = 1
        """  , as_dict = True)
        if penalties:
            entry = {
                'supplier' : self.supplier, 
                'purchase_receipt' : self.name , 
                'posting_date' : self.posting_date,
                'penalties' : penalties
            }
            frappe.new_doc('Penalty Entry').update(entry).insert(ignore_permissions = True).submit()

def check_request_to_accepted_qty(self): 
    for i in self.items: 
        if flt(i.qty) + flt(i.rejected_qty) > flt(i.custom_request_quantity) and i.custom_purchase_request not in [None, '']:
            frappe.throw(
                _("""The total of Accepted Qty ({0}) and Rejected Qty ({1}) cannot exceed the Requested Quantity ({2}) for item {3}.
                """.format(flt(i.qty) ,flt(i.rejected_qty) , flt(i.custom_request_quantity) , i.item_code)
            ))

        
def validate_qty(self):
    """Validates qty at row level"""
    self.item_allowance = {}
    self.global_qty_allowance = None
    self.global_amount_allowance = None

    for args in self.status_updater:
        if "target_ref_field" not in args:
            continue
        for d in self.get_all_children():
            if (hasattr(d, "qty") and d.qty < 0 and not self.get("is_return")) or hasattr(d, "custom_request_quantity") and d.custom_request_quantity < 0 and not self.get("is_return"):
                frappe.throw(_("For an item {0}, quantity must be positive number").format(d.item_code))

            if (hasattr(d, "qty") and d.qty > 0 and self.get("is_return")) or hasattr(d, "custom_request_quantity") and d.custom_request_quantity > 0 and self.get("is_return"):
                frappe.throw(_("For an item {0}, quantity must be negative number").format(d.item_code))

            if not frappe.db.get_single_value("Selling Settings", "allow_negative_rates_for_items"):
                if hasattr(d, "item_code") and hasattr(d, "rate") and flt(d.rate) < 0:
                    frappe.throw(
                        _(
                            "For item {0}, rate must be a positive number. To Allow negative rates, enable {1} in {2}"
                        ).format(
                            frappe.bold(d.item_code),
                            frappe.bold(_("`Allow Negative rates for Items`")),
                            get_link_to_form("Selling Settings", "Selling Settings"),
                        ),
                    )
            if d.doctype == args["source_dt"] and d.get(args["join_field"]):
                args["name"] = d.get(args["join_field"])
                item = frappe.db.sql(
                    """select item_code, `{target_ref_field}`,
                    `{target_field}`, parenttype, parent from `tab{target_dt}`
                    where name=%s and docstatus=1""".format(**args),
                    args["name"],
                    as_dict=1,
                )
                if item:
                    item = item[0]
                    item["idx"] = d.idx
                    item["target_ref_field"] = args["target_ref_field"].replace("_", " ")
                    item["received_qty"] = flt(d.get("custom_request_quantity"))
                    if args.get("no_allowance"):
                        item["reduce_by"] = item[args["target_field"]] - item[args["target_ref_field"]]
                        if item["reduce_by"] > 0.01:
                            limits_crossed_error(self , args, item, "qty")
                    elif item[args["target_ref_field"]]:
                        check_overflow_with_allowance(self , item, args)
def set_purchase_order_rate(self):
    if self.is_return == 1 :
        return
    for i in self.items:
        i.rate = flt(frappe.db.get_value('Purchase Order Item' , i.purchase_order_item , 'rate'))
        request_status = frappe.db.get_value('Purchase Request' , i.custom_purchase_request , 'status')
        if request_status == 'Closed':
            frappe.throw(_('Cannot create Purchase Receipt against a closed Purchase Request: {0}').format(i.custom_purchase_request))
        
        
def update_received_qty(doc):

    for item in doc.items:
        if item.custom_purchase_request and item.custom_purchase_request_item:
            pr_item = frappe.get_doc("Purchase Request Item", item.custom_purchase_request_item)
            pr_item.received_qty = flt(pr_item.received_qty) + flt(item.qty)
            pr_item.save(ignore_permissions=True)
    if doc.items[0].custom_purchase_request:
        pr = frappe.get_doc("Market Purchase Request", doc.items[0].custom_purchase_request)
        total_requested = sum(flt(i.request_quantity) for i in pr.items)
        total_received = sum(flt(i.received_qty) for i in pr.items)
        pr.status = "Completed" if total_received >= total_requested else "To Receive"
        pr.save(ignore_permissions=True) #
        
def update_received_qty_on_cancel(doc):
    for item in doc.items:
        if item.custom_purchase_request and item.custom_purchase_request_item:
            pr_item = frappe.get_doc("Purchase Request Item", item.custom_purchase_request_item)
            pr_item.received_qty = flt(pr_item.received_qty) - flt(item.qty)
            if pr_item.received_qty < 0:
                pr_item.received_qty = 0
            pr_item.save(ignore_permissions=True)
    if doc.items[0].custom_purchase_request:
        pr = frappe.get_doc("Market Purchase Request", doc.items[0].custom_purchase_request)
        total_requested = sum(flt(i.request_quantity) for i in pr.items)
        total_received = sum(flt(i.received_qty) for i in pr.items)
        pr.status = "Completed" if total_received >= total_requested else "To Receive"
        pr.save(ignore_permissions=True)
        
def validate_inspection_status(self):
    item_codes = [d.item_code for d in self.items]
    inspection_statuses = get_inspection_status(item_codes)

    invalid_items = [
        (item.item_code, inspection_statuses.get(item.item_code))
        for item in self.items
        if inspection_statuses.get(item.item_code)
        and inspection_statuses.get(item.item_code) != "Accepted"
    ]

    if invalid_items:
        msg = "<br>".join(
            _("Item {0} has inspection status '{1}' which does not allow it to be included.")
            .format(code, status)
            for code, status in invalid_items
        )
        if self.docstatus == 1 :
            frappe.throw(msg)
        else:
            frappe.msgprint(msg)
        
        
def validate_some_markets_warehouse(self):
    if not self.items:
        return
    warehouse = self.set_warehouse
    if not warehouse:
        msg = _("Please set Warehouse before validating Item Markets restrictions.")
        if self.docstatus == 1 :
            frappe.throw(msg)
        else:
            frappe.msgprint(msg)
    wh_type = frappe.db.get_value("Warehouse", warehouse, "warehouse_type") if warehouse else None
    if wh_type not in ("Store", "سوق"):
        return 
    for row in self.items:
        item_code = row.item_code
        row_warehouse = row.warehouse or warehouse
        has_restriction = frappe.db.exists(
            "Item Markets",{"item_code": item_code,"disabled": 0})
        if has_restriction:
            allowed = frappe.db.exists(
                "Item Markets",{"item_code": item_code,"warehouse": row_warehouse,"disabled": 0})
            if not allowed:
                msg = _(
                        "Row #{0}: Item <b>{1}</b> is not allowed in Warehouse <b>{2}</b> as per Item Markets."
                    ).format(row.idx, item_code, row_warehouse)
                if self.docstatus == 1 :
                    frappe.throw(msg)
                else:
                    frappe.msgprint(msg)



@frappe.whitelist()
def create_material_inspection(source_name, target_doc=None, args=None):
    if args is None:
        args = {}
    if isinstance(args, str):
        args = json.loads(args)
    def update_item(source, target, source_parent):
        target.item_code = source.item_code
        target.item_name = source.item_name
        target.description = source.description
        target.quantity_supplied = flt(source.qty)
        target.batch_number = source.batch_no
        target.production_date = None
        target.expiry_date = None

    def select_item(d):
        filtered_items = args.get("filtered_children", [])
        return d.name in filtered_items if filtered_items else True
    doc = get_mapped_doc(
        "Purchase Receipt",
        source_name,
        {
            "Purchase Receipt": {
                "doctype": "Material Inspection",
                "field_map": {
                    "name": "purchase_receipt",
                    "company": "company"
                },
                "validation": {
                    "docstatus": ["=", 0],
                },
            },
            "Purchase Receipt Item": {
                "doctype": "Material Inspection Details",
                "field_map": {
                    "parent": "purchase_receipt",
                    "name": "purchase_receipt_item"
                },
                "postprocess": update_item,
                "condition": lambda doc: select_item(doc),
            },
        },
        target_doc
    )
    return doc
