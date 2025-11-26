# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe 
from frappe.model.document import Document
from masar_mce.utils import get_tax_for_item , get_standard_price_list_buying_then_selling , get_current_stock_value_and_quantity
from frappe.utils import flt
from frappe import _
from datetime import datetime
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_by_blanket_order(doctype, txt, searchfield, start, page_len, filters):
    blanket_order = filters.get('blanket_order')
    if not blanket_order:
        return []
    query = """
        SELECT DISTINCT tboi.item_code, tboi.item_name
        FROM `tabBlanket Order Item` tboi
        WHERE 
            tboi.docstatus = 1
            AND tboi.parent = %(blanket_order)s
            AND (
                tboi.item_code LIKE %(txt)s
                OR tboi.item_name LIKE %(txt)s
            )
        ORDER BY tboi.idx
        LIMIT %(start)s, %(page_len)s
    """
    return frappe.db.sql(query, {
        'blanket_order': blanket_order,
        'txt': f"%{txt}%",
        'start': start,
        'page_len': page_len
    })

@frappe.whitelist()
def get_items_for_dialog(blanket_order):
    if not blanket_order:
        frappe.throw("Please select a Supplier Agreement first.")
    items = frappe.get_all(
        "Blanket Order Item",
        filters={"parent": blanket_order},
        fields=["item_code","item_name" ,"rate","custom_selling_price_after_tax", "custom_purchase_price_after_tax", "custom_markup_percentage", "custom_selling_price"]
    )

    return items

class PricingSheet(Document):
	def validate(self): 
		self.calculate_pricing_after_tax_and_there_totals()
		self.validate_items_from_blanket_order()
		self.validate_duplicate_items()
  
	def on_cancel(self):
		self.close_valid_date_in_item_price()
	
	def on_submit(self): 
		self.create_item_prices_for_every_item()
	def calculate_pricing_after_tax_and_there_totals(self):
		total_rate = total_rate_after_tax = total_selling_price = total_selling_price_after_tax = 0 
		for i in self.items:
			tax_rate = flt(get_tax_for_item(item_code= i.item_code))
			current = self.get_stock_value_and_quantity(i)
			i.current_stock_value = current.get("value", 0)
			i.current_quantity = current.get("quantity", 0)
			i.rate = flt(flt(i.current_stock_value) + flt(i.new_purchase_price) * flt(i.new_quantity)) / (flt(i.current_quantity) + flt(i.new_quantity)
                                                                                                 ) if (flt(i.current_quantity) + flt(i.new_quantity)) > 0 else 0
			i.tax_rate = tax_rate * 100 
			i.rate_after_tax = flt(i.rate) + flt(i.rate) * tax_rate 
			i.selling_price_after_tax = flt(i.selling_price) + flt(i.selling_price) * tax_rate 
			total_rate+= flt(i.rate)
			total_rate_after_tax += flt(i.rate_after_tax) 
			total_selling_price += flt(i.selling_price)
			total_selling_price_after_tax += flt(i.selling_price_after_tax)
		self.total_purchase_price , self.total_purchase_price_after_tax = total_rate , total_rate_after_tax
		self.total_selling_price  , self.total_selling_price_after_tax = total_selling_price , total_selling_price_after_tax
	def validate_items_from_blanket_order(self):
		if not self.blanket_order:
			frappe.throw(_("Please select a Supplier Agreement before adding items."))
		allowed_items = [i.item_code for i in frappe.db.get_values(
            "Blanket Order Item",
            {"parent": self.blanket_order},
            "item_code",
            as_dict=True
        )]
		for row in self.items:
			if row.item_code not in allowed_items:
				frappe.throw(
                _("Item <b>{0}</b> is not part of Supplier Agreement <b>{1}</b>.").format(row.item_code , self.blanket_order)
            	)
	def validate_duplicate_items(self):
		seen = set()
		duplicates = []

		for row in self.items:
			if row.item_code in seen:
				duplicates.append(row.item_code)
			seen.add(row.item_code)
		if duplicates:
			frappe.throw(
				"Duplicate items found: " + ", ".join(set(duplicates))
			)
   
	def create_item_prices_for_every_item(self): 
		buying , selling = get_standard_price_list_buying_then_selling()
		for i in self.items:
			if i.rate > i.selling_price:
				frappe.throw(_("Row #{0}: Rate cannot be greater than Selling Price for item {1}").format(i.idx, i.item_code))
			ip_buy = frappe.new_doc("Item Price")
			ip_buy.item_code = i.item_code
			ip_buy.price_list = buying
			ip_buy.price_list_rate = i.rate
			ip_buy.valid_from = self.posting_date
			ip_buy.custom_supplier_agreement = self.blanket_order
			ip_buy.custom_pricing_sheet = self.name
			ip_buy.insert(ignore_permissions=True)
			ip_sell = frappe.new_doc("Item Price")
			ip_sell.item_code = i.item_code
			ip_sell.price_list = selling
			ip_sell.price_list_rate = i.selling_price
			ip_sell.valid_from = self.posting_date
			ip_sell.custom_supplier_agreement = self.blanket_order
			ip_sell.custom_pricing_sheet = self.name
			ip_sell.insert(ignore_permissions=True)
   
	def close_valid_date_in_item_price(self):
		item_price_list = frappe.db.get_list('Item Price' , filters={'custom_pricing_sheet': self.name},pluck='name' )
		for i in item_price_list: 
			ip_doc = frappe.get_doc('Item Price' , i)
			ip_doc.valid_upto = datetime.now().date()
			ip_doc.save()
   
	@frappe.whitelist()
	def get_last_sync(self):
		sql = frappe.db.sql("""
        	SELECT 
    			CONCAT(
        			posting_date, ' ', 
        			(	
           				SELECT 
               				MAX(posting_time) 
         				FROM 
             				`tabAPI Data Income` 
         				WHERE 
             				posting_date = t.posting_date
                 	)
    			) AS last_sync_datetime
			FROM 
   				`tabAPI Data Income` t
			WHERE 
   				posting_date = (
    				SELECT 
        				MAX(posting_date) 
    				FROM 
        				`tabAPI Data Income`
				)
			LIMIT 
   				1""")
		if self.docstatus == 0:
			if sql and sql[0][0]:
				return datetime.strptime(str(sql[0][0]), "%Y-%m-%d %H:%M:%S.%f")
		return None
	@frappe.whitelist()
	def get_stock_value_and_quantity(self, row):
		return get_current_stock_value_and_quantity(item_code=row.get('item_code'))