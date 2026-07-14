# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe, json
from frappe.model.document import Document
from frappe.utils import flt, fmt_money , get_datetime
from frappe.model.mapper import get_mapped_doc
from masar_mce.utils import get_inspection_status
from frappe import _

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
            f"<b>Qty:</b> {fmt_money(row.available_qty, currency=None)}<br>"
        )
        for row in result
    ]


@frappe.whitelist()
def get_po_details_for_item(item_code, supplier, used_pos=None):
    if used_pos is None:
        used_pos = []
    if isinstance(used_pos, str):
        try:
            used_pos = json.loads(used_pos)
        except:
            used_pos = []

    query = f"""
        SELECT
            po.name AS purchase_order,
            poi.name AS purchase_order_item,
            poi.rate AS rate,
            poi.stock_uom as uom,
            (poi.qty - IFNULL(poi.received_qty,0) 
                - IFNULL((
                    SELECT SUM(pri.request_quantity - IFNULL(pri.received_qty,0))
                    FROM `tabPurchase Request Item` pri
                    WHERE pri.purchase_order_item = poi.name AND pri.docstatus = 1
                ),0)
                + poi.qty * IFNULL(item.over_delivery_receipt_allowance,0)
            ) AS available_qty
        FROM `tabPurchase Order` po
        INNER JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
        INNER JOIN `tabItem` item ON poi.item_code = item.name
        WHERE po.supplier = '{supplier}'
          AND po.docstatus = 1
          AND po.status NOT IN ('Closed','Hold')
          AND poi.item_code = '{item_code}'
          AND (poi.qty - IFNULL(poi.received_qty,0)
               - IFNULL((
                    SELECT SUM(pri.request_quantity - IFNULL(pri.received_qty,0))
                    FROM `tabPurchase Request Item` pri
                    WHERE pri.purchase_order_item = poi.name AND pri.docstatus = 1
               ),0)
               + poi.qty * IFNULL(item.over_delivery_receipt_allowance,0)
          ) > 0
    """
    if used_pos:
        pos_not_in = ", ".join([f"'{p}'" for p in used_pos])
        query += f" AND po.name NOT IN ({pos_not_in})"
    query += " ORDER BY po.transaction_date, po.name LIMIT 1"

    result = frappe.db.sql(query, as_dict=True)
    return result[0] if result else {}


@frappe.whitelist()
def make_purchase_request(source_name, target_doc=None, args=None):
    if args is None:
        args = {}
    if isinstance(args, str):
        args = json.loads(args)

    def update_item(source, target, source_parent):
        # over_delivery = flt(frappe.db.get_value("Item", source.item_code, "over_delivery_receipt_allowance") or 0)
        # pending_pr_qty = flt(frappe.db.sql("""
        #     SELECT SUM(pri.request_quantity - IFNULL(pri.received_qty,0))
        #     FROM `tabPurchase Request Item` pri
        #     WHERE pri.purchase_order_item = %s AND pri.docstatus = 1
        # """, source.name)[0][0] or 0)
        qty =0 # flt(source.qty) - flt(source.received_qty or 0) - pending_pr_qty + flt(source.qty) * over_delivery
        target.request_quantity = qty
        target.rate = flt(source.rate)
        target.amount = qty * flt(source.rate)
        target.purchase_order = source_parent.name
        target.purchase_order_item = source.name
    def select_item(d):
        filtered_items = args.get("filtered_children", [])
        return d.name in filtered_items if filtered_items else True
    doc = get_mapped_doc(
        "Purchase Order",
        source_name,
        {
            "Purchase Order": {
                "doctype": "Market Purchase Request",
                "validation": {"docstatus": ["=", 1]},
            },
            "Purchase Order Item": {
                "doctype": "Purchase Request Item",
                "field_map": {
                    "item_code": "item_code",
                    "item_name": "item_name",
                    "item_group": "item_group",
                    "uom": "uom",
                },
                "postprocess": update_item,
                "condition": lambda doc: select_item(doc),
            },
        },
        target_doc
    )
    return doc
@frappe.whitelist()
def make_purchase_receipt_from_purchase_request(source_name, target_doc=None):
    pr = frappe.get_doc("Market Purchase Request", source_name)
    if not pr.items:
        frappe.throw(_("No items found in Market Purchase Request"))
    
    po_items_map = {}
    for item in pr.items:
        if not item.purchase_order:
            frappe.throw(_("Item {0} has no linked Purchase Order".format(item.item_code)))
        po_items_map.setdefault(item.purchase_order, []).append(item)
    
    receipts = []
    
    for po_name, items in po_items_map.items():
        def update_item(po_item, pr_item, source_parent):
            matched_items = [i for i in items if i.purchase_order_item == po_item.name]
            total_remaining_qty = 0
            for req_item in matched_items:
                remaining_qty = flt(req_item.request_quantity) - flt(req_item.received_qty)
                if remaining_qty > 0:
                    total_remaining_qty += remaining_qty
            if total_remaining_qty <= 0:
                return None
            pr_item.qty = total_remaining_qty
            pr_item.rate = flt(po_item.rate)
            pr_item.amount = pr_item.qty * pr_item.rate
            pr_item.custom_request_quantity = total_remaining_qty
            pr_item.purchase_order = po_name
            pr_item.purchase_order_item = po_item.name
            pr_item.custom_purchase_request = pr.name
            pr_item.custom_purchase_request_item = matched_items[0].name if matched_items else None
            pr_item.warehouse = pr.set_warehouse or frappe.throw(
                "Please set 'Accepted Warehouse' in Purchase Request"
            )
            return pr_item
        doc = get_mapped_doc(
            "Purchase Order",
            po_name,
            {
                "Purchase Order": {
                    "doctype": "Purchase Receipt",
                    "validation": {"docstatus": ["=", 1]},
                    "field_map": {
                        "supplier": "supplier",
                        "supplier_name": "supplier_name",
                        "set_warehouse": "set_warehouse",
                        "custom_request_date": "request_date",
                    },
                },
                "Purchase Order Item": {
                    "doctype": "Purchase Receipt Item",
                    "condition": lambda d: any(
                        i.purchase_order_item == d.name 
                        for i in items 
                        if (flt(i.request_quantity) - flt(i.received_qty)) > 0
                    ),
                    "postprocess": update_item,
                },
            },
            target_doc
        )
        doc.items = [item for item in doc.items if item is not None]
        for i, item in enumerate(doc.items, start=1):
            item.idx = i
        
        doc.set_warehouse = pr.set_warehouse
        receipts.append(doc)
    if len(receipts) == 1:
        return receipts[0]
    else:
        first = receipts[0]
        for r in receipts[1:]:
            for item in r.items:
                first.append("items", item)
        for i, item in enumerate(first.items, start=1):
            item.idx = i
        
        return first



class MarketPurchaseRequest(Document):

    def validate(self):
        self.get_po_details_for_item_on_validate()
        self.validate_po_available_qty()
        self.validate_inspection_status()
        self.validate_some_markets_warehouse()
        self.get_total_and_total_qty()
    def on_submit(self):
        self.db_set('status', 'To Receive')
        self.set_order_qty_in_purchase_order()
        self.send_email_to_supplier()
    def on_cancel(self):
        self.db_set('status', 'Cancelled')
        self.revert_order_qty_in_purchase_order()
    def get_po_details_for_item_on_validate(self):
        if not self.supplier:
            return
        used_pos_map = {}

        for item in self.items:
            if not item.item_code:
                continue
            if not item.item_name or not item.item_group or not item.description:
                item_data = frappe.db.get_value(
                    "Item",
                    item.item_code,
                    ["item_name", "item_group", "description"],
                    as_dict=True,
                )
                if item_data:
                    if not item.item_name:
                        item.item_name = item_data.item_name
                    if not item.item_group:
                        item.item_group = item_data.item_group
                    if not item.description:
                        item.description = item_data.description
            used_pos = used_pos_map.get(item.item_code, [])
            values = [self.supplier, item.item_code]
            exclude_clause = ""
            if used_pos:
                placeholders = ", ".join(["%s"] * len(used_pos))
                exclude_clause = f" AND po.name NOT IN ({placeholders})"
                values.extend(used_pos)
            result = frappe.db.sql(f"""
                SELECT
                    po.name AS purchase_order,
                    poi.name AS purchase_order_item,
                    poi.rate AS rate,
                    poi.stock_uom AS uom
                FROM `tabPurchase Order` po
                INNER JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
                INNER JOIN `tabItem` item ON poi.item_code = item.name
                WHERE po.supplier = %s
                  AND po.docstatus = 1
                  AND po.status NOT IN ('Closed', 'Hold')
                  AND poi.item_code = %s
                  AND (
                        poi.qty - IFNULL(poi.received_qty, 0)
                        - IFNULL((
                            SELECT SUM(pri.request_quantity - IFNULL(pri.received_qty, 0))
                            FROM `tabPurchase Request Item` pri
                            WHERE pri.purchase_order_item = poi.name AND pri.docstatus = 1
                        ), 0)
                        + poi.qty * IFNULL(item.over_delivery_receipt_allowance, 0)
                  ) > 0
                {exclude_clause}
                ORDER BY po.transaction_date, po.name
                LIMIT 1
            """, values, as_dict=True)
            if result:
                po = result[0]
                item.purchase_order = po.purchase_order
                item.purchase_order_item = po.purchase_order_item
                item.rate = po.rate
                if not item.uom:
                    item.uom = po.uom
                used_pos_map.setdefault(item.item_code, []).append(po.purchase_order)
            else:
                if item.purchase_order:
                    po_supplier = frappe.db.get_value("Purchase Order", item.purchase_order, "supplier")
                    po_status = frappe.db.get_value("Purchase Order", item.purchase_order, "status")
                    if po_supplier != self.supplier:
                        msg = (
                            _("Row {0}: Purchase Order {1} belongs to supplier <b>{2}</b>, not the selected supplier <b>{3}</b>.").format(
                                item.idx, item.purchase_order, po_supplier, self.supplier
                            )
                        )
                        if self.docstatus == 1:
                            frappe.throw(msg)
                        else:
                            frappe.msgprint(msg)
                    if po_status in ("Closed", "On Hold"):
                        msg = (
                            _("Row {0}: Purchase Order {1} is <b>{2}</b> and cannot be used.").format(
                                item.idx, item.purchase_order, po_status
                            )
                        )
                        if self.docstatus == 1:
                            frappe.throw(msg)
                        else:
                            frappe.msgprint(msg)
                msg = (
                    _("Row {0}: No available open Purchase Order found for item <b>{1}</b> with supplier <b>{2}</b>.").format(
                        item.idx, item.item_code, self.supplier
                    )
                )
                if self.docstatus == 1:
                    frappe.throw(msg)
                else:
                    frappe.msgprint(msg)

    def get_total_and_total_qty(self):
        total = 0
        total_qty = 0
        for item in self.items:
            item.amount = flt(item.request_quantity) * flt(item.rate)
            total += flt(item.amount)
            total_qty += flt(item.request_quantity)
        self.total = total
        self.total_quantity = total_qty
    def validate_po_available_qty(self):
        for item in self.items:

            if not item.purchase_order_item:
                continue
            po_item = frappe.get_doc(
                "Purchase Order Item", item.purchase_order_item
            )

            po_qty = flt(po_item.qty)
            received_qty = flt(po_item.received_qty)
            already_requested = frappe.db.sql("""
                SELECT SUM(pri.request_quantity - IFNULL(pri.received_qty,0))
                FROM `tabPurchase Request Item` pri
                INNER JOIN `tabMarket Purchase Request` pr
                    ON pr.name = pri.parent
                WHERE
                    pri.purchase_order_item = %s
                    AND pr.docstatus = 1
                    AND pr.name != %s
            """, (item.purchase_order_item, self.name))[0][0] or 0
            over_delivery = flt(
                frappe.db.get_value(
                    "Item", item.item_code, "over_delivery_receipt_allowance"
                ) or 0
            )
            allowed_qty = (
                flt(po_qty)
                - flt(received_qty)
                - flt(already_requested)
                + flt(po_qty) * flt(over_delivery)
            )
            if flt(item.request_quantity) > allowed_qty:
                frappe.throw(
                    _(
                        "Row <b>{6}</b>:Item <b>{0}</b><br><br>"
                        "Requested Qty: <b>{1}</b><br>"
                        "Available Qty: <b>{2}</b><br><br>"
                        "PO Qty: {3}<br>"
                        "Received: {4}<br>"
                        "Requested in other PRs: {5}"
                    ).format(
                        item.item_code,
                        item.request_quantity,
                        allowed_qty,
                        po_qty,
                        received_qty,
                        already_requested,
                        item.idx,
                    ),
                    title=_("Purchase Order Quantity Exceeded"),
                )
    def set_order_qty_in_purchase_order(self):
        for item in self.items:
            if item.purchase_order_item and flt(item.request_quantity):
                current_qty = flt(frappe.db.get_value(
                    "Purchase Order Item",
                    item.purchase_order_item,
                    "custom_ordered_qty"
                )) or 0

                frappe.db.set_value(
                    "Purchase Order Item",
                    item.purchase_order_item,
                    "custom_ordered_qty",
                    current_qty + flt(item.request_quantity),
                    update_modified=False
                )
    def revert_order_qty_in_purchase_order(self):
        for item in self.items:
            if item.purchase_order_item and flt(item.request_quantity):
                current_qty = flt(frappe.db.get_value(
                    "Purchase Order Item",
                    item.purchase_order_item,
                    "custom_ordered_qty"
                )) or 0

                new_qty = current_qty - flt(item.request_quantity)

                frappe.db.set_value(
                    "Purchase Order Item",
                    item.purchase_order_item,
                    "custom_ordered_qty",
                    max(new_qty, 0),
                    update_modified=False
                )
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
            has_restriction = frappe.db.exists(
                "Item Markets",{"item_code": item_code,"disabled": 0})
            if has_restriction:
                allowed = frappe.db.exists(
                    "Item Markets",{"item_code": item_code,"warehouse": warehouse,"disabled": 0})
                if not allowed:
                    msg =  _(
                            "Row #{0}: Item <b>{1}</b> is not allowed in Warehouse <b>{2}</b> as per Item Markets."
                        ).format(row.idx, item_code, warehouse)
                    if self.docstatus == 1 :
                        frappe.throw(msg)
                    else:
                        frappe.msgprint(msg)
    def send_email_to_supplier(self):
        if not self.supplier:
            return
        supplier_email = (
            frappe.db.get_value("Supplier", self.supplier, "email_id")
            or frappe.db.get_value("Supplier", self.supplier, "custom_email")
        )
        if not supplier_email:
            frappe.msgprint(
                _("Supplier {0} does not have an email address.").format(self.supplier)
            )
            return
        supplier_name = self.supplier_name or self.supplier
        warehouse = self.set_warehouse or ""
        request_date = frappe.format(self.request_date, {"fieldtype": "Date"})
        modified_time = get_datetime(self.modified).strftime("%H:%M")
        email_message = f"""
            <html>
            <body style="margin:0;padding:0;">
            <div dir="rtl"
                style="
                    direction: rtl;
                    unicode-bidi: embed;
                    text-align: right;
                    font-family: Tahoma, Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.8;
                    color: #1f2937;
                ">

                <p style="margin:0 0 15px 0;">
                    السادة <strong>{supplier_name}</strong> المحترمين،
                </p>

                <p style="margin:0 0 15px 0;">
                    تحية طيبة وبعد،
                </p>

                <p style="margin:0 0 20px 0;">
                    نود إشعاركم بأنه تم إصدار
                    <strong>وصل استلام طلبية أسواق</strong>
                    رقم <strong>{self.name}</strong>.
                </p>

                <table cellpadding="8" cellspacing="0"
                    style="
                            width:100%;
                            border-collapse:collapse;
                            background:#f8f9fa;
                            border-right:4px solid #1f2937;
                            margin:20px 0;
                            direction:rtl;
                            text-align:right;
                    ">
                    <tr>
                        <td><strong>المستلم:</strong></td>
                        <td>{warehouse}</td>
                    </tr>
                    <tr>
                        <td><strong>تاريخ ووقت الطلب:</strong></td>
                        <td>{request_date} - {modified_time}</td>
                    </tr>
                </table>

                <p style="margin:20px 0;">
                    تجدون مرفقًا نسخة PDF من وصل الاستلام، والتي تتضمن جميع التفاصيل والبيانات الخاصة بالوصل، وذلك للاعتماد والطباعة والاحتفاظ بها كسجل رسمي.
                </p>

                <br>

                <p style="margin:0;">
                    مع خالص الشكر والتقدير،
                </p>

                <p style="margin-top:10px;">
                    <strong>المؤسسة الاستهلاكية العسكرية</strong><br>
                    القيادة العامة للقوات المسلحة الأردنية - الجيش العربي
                </p>

            </div>
            </body>
            </html>
            """

        subject = _("تم اعتماد طلبية الشراء {0}").format(self.name)

        pdf_attachment = frappe.attach_print(self.doctype, self.name, doc=self)

        try:
            frappe.sendmail(
                recipients=[supplier_email],
                subject=subject,
                message=email_message,
                reference_doctype=self.doctype,
                reference_name=self.name,
                attachments=[pdf_attachment],
                now=True,
            )
            frappe.msgprint(_("Email sent successfully to {0}.").format(supplier_email), alert=True)

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Market Purchase Request Email"
            )
            frappe.sendmail(
                recipients=[supplier_email],
                subject=subject,
                message=email_message,
                reference_doctype=self.doctype,
                reference_name=self.name,
                attachments=[pdf_attachment],
                now=False,
            )
            frappe.msgprint(
                _("Unable to send the email immediately. It has been queued for delivery."), alert=True
            )