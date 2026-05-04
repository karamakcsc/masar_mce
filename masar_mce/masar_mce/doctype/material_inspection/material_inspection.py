# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate
from dateutil.relativedelta import relativedelta

class MaterialInspection(Document):
    def calculate_child_row(self, row):
        """Update delay_period (Int), product_lifespan (Duration), production_exceeded (Percent)"""
        supply_date = getdate(row.supply_date) if row.supply_date else None
        production_date = getdate(row.production_date) if row.production_date else None
        expiry_date = getdate(row.expiry_date) if row.expiry_date else None
        if supply_date and production_date:
            delta = supply_date - production_date
            row.delay_period = delta.days
        else:
            row.delay_period = None
        if production_date and expiry_date:
            diff = relativedelta(expiry_date, production_date)
            years = diff.years
            months = diff.months
            parts = []
            if years:
                parts.append(f"{years} year{'s' if years != 1 else ''}")
            if months:
                parts.append(f"{months} month{'s' if months != 1 else ''}")
            lifespan_str = " ".join(parts) if parts else "0 months"
            row.product_lifespan = lifespan_str 
        else:
            row.product_lifespan = None
        if supply_date and production_date and expiry_date:
            total_lifespan = (expiry_date - production_date).days
            if total_lifespan > 0:
                used_days = (supply_date - production_date).days
                percentage = (used_days / total_lifespan) * 100
                row.production_exceeded = round(percentage, 2)
            else:
                row.production_exceeded = None
        else:
            row.production_exceeded = None
	
   
    @frappe.whitelist()
    def get_selling_price_from_supplier_agreement(self, item_code, supplier):
        if not item_code or not supplier:
            return {}
        result = frappe.db.sql(
            """
            SELECT boi.custom_selling_price as selling_price  
            FROM `tabBlanket Order` bo
            INNER JOIN `tabBlanket Order Item` boi ON bo.name = boi.parent
            WHERE bo.supplier = %(supplier)s
            AND bo.docstatus = 1
            AND bo.custom_status = 'Active'
            AND boi.item_code = %(item_code)s
            LIMIT 1
            """,
            {"supplier": supplier, "item_code": item_code},
            as_dict=True
        )
        return result[0] if result else {}
    def validate(self):
        if self.purchase_receipt:
            pr_doc = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
            if pr_doc.docstatus != 0:
                frappe.throw(_("Purchase Receipt {0} must be in Draft status. Current status: {1}").format(
					self.purchase_receipt, "Draft" if pr_doc.docstatus == 0 else "Submitted/Cancelled"
				))
            pr_items = {item.item_code for item in pr_doc.items}
            seen_items = set()
            for row in self.get("items"):
                if row.item_code:
                    if row.item_code in seen_items:
                        frappe.throw(_("Item {0} is duplicated in the inspection items. Please remove duplicates.").format(row.item_code))
                    seen_items.add(row.item_code)
                    if row.item_code not in pr_items:
                        frappe.throw(_("Item {0} is not present in Purchase Receipt {1}").format(
							row.item_code, self.purchase_receipt
						))
        for row in self.get("items"):
            self.calculate_child_row(row)
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_from_purchase_receipt(doctype, txt, searchfield, start, page_len, filters):
    purchase_receipt = filters.get("purchase_receipt")
    if not purchase_receipt:
        return []
    pr_doc = frappe.get_doc("Purchase Receipt", purchase_receipt)
    if pr_doc.docstatus != 0:
        frappe.throw(_("Purchase Receipt {0} is not in Draft status").format(purchase_receipt))
    items = frappe.db.sql("""
        SELECT 
            pri.item_code,
            IFNULL(pri.item_name, it.item_name) as item_name
        FROM `tabPurchase Receipt Item` pri
        LEFT JOIN `tabItem` it ON pri.item_code = it.name
        WHERE pri.parent = %(pr)s
            AND (pri.item_code LIKE %(txt)s OR pri.item_name LIKE %(txt)s)
        ORDER BY pri.item_code
        LIMIT %(start)s, %(page_len)s
    """, {
        "pr": purchase_receipt,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    }, as_list=False) 
    return [(item[0], item[1]) for item in items] if items else []