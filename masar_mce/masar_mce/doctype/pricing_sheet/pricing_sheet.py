# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe 
from frappe.model.document import Document
from masar_mce.utils import get_tax_for_item , get_standard_price_list_b_s_sfz , get_current_stock_value_and_quantity , get_item_barcode
from frappe.utils import flt
from frappe import _ , get_doc , db
from datetime import datetime
from masar_mce.api import insert_pos_item
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
		self.create_pos_item()
	def calculate_pricing_after_tax_and_there_totals(self):
			new_total_quantity = local_sa = free_sa = new_purchase_amount = 0
			for i in self.items:
				free_tax_rate = get_tax_for_item(i.item_code, 'Free Zone')
				local_tax_rate = get_tax_for_item(i.item_code, 'Local Zone')
				local_stock = get_current_stock_value_and_quantity(i.item_code, cost_zone='Local Zone')
				free_stock = get_current_stock_value_and_quantity(i.item_code, cost_zone='Free Zone')
				i.local_curr_qty = flt(local_stock.get("quantity", 0))
				i.local_curr_stock_value = flt(local_stock.get("stock_value", 0))
				i.local_curr_val_rate = flt(local_stock.get("valuation_rate", 0))
				i.free_curr_qty = flt(free_stock.get("quantity", 0))
				i.free_curr_stock_value = flt(free_stock.get("stock_value", 0))
				i.free_curr_cal_rate = flt(free_stock.get("valuation_rate", 0))
				i.global_curr_stock_value = flt(i.local_curr_stock_value) + flt(i.free_curr_stock_value)
				i.global_new_stock_value = flt(i.global_curr_stock_value) + (flt(i.new_purchase_price) * flt(i.new_quantity))
				total_quantity = flt(i.local_curr_qty) + flt(i.free_curr_qty) + flt(i.new_quantity)
				i.global_val_rate = i.global_new_stock_value / total_quantity if total_quantity > 0 else 0
				i.local_tax_rate = local_tax_rate * 100
				i.free_tax_rate = free_tax_rate * 100
				local_tax_decimal = local_tax_rate
				free_tax_decimal = free_tax_rate
				if not i.local_sp and i.local_sp_after_tax:
					i.local_sp = flt(i.local_sp_after_tax) / (1 + local_tax_decimal)
				elif i.local_sp and not i.local_sp_after_tax:
					i.local_sp_after_tax = flt(i.local_sp) * (1 + local_tax_decimal)
				if not i.free_sp and i.free_sp_after_tax:
					i.free_sp = flt(i.free_sp_after_tax) / (1 + free_tax_decimal)
				elif i.free_sp and not i.free_sp_after_tax:
					i.free_sp_after_tax = flt(i.free_sp) * (1 + free_tax_decimal)		
				if self.pricing_type == "Buying Price Basis":
					i.local_pp_after_tax = flt(i.new_purchase_price) * (1 + local_tax_decimal)
					i.free_pp_after_tax = flt(i.new_purchase_price) * (1 + free_tax_decimal)		
					if flt(i.local_mp) or flt(i.local_mp) == 0:
						if flt(i.local_mp) == -100:
							i.local_sp = 0
						else:
							i.local_sp = flt(i.local_pp_after_tax) * (1 + flt(i.local_mp) / 100)
					else:
						i.local_sp = flt(i.local_pp_after_tax)
					
					if flt(i.free_mp) or flt(i.free_mp) == 0:
						if flt(i.free_mp) == -100:
							i.free_sp = 0
						else:
							i.free_sp = flt(i.free_pp_after_tax) * (1 + flt(i.free_mp) / 100)
					else:
						i.free_sp = flt(i.free_pp_after_tax)
					i.local_sp_after_tax = flt(i.local_sp) * (1 + local_tax_decimal)
					i.free_sp_after_tax = flt(i.free_sp) * (1 + free_tax_decimal)
						
				elif self.pricing_type == "Selling Price Basis":
					if flt(i.local_sp):
						i.local_sp_after_tax = flt(i.local_sp) * (1 + local_tax_decimal)
						
						if flt(i.local_mp) or flt(i.local_mp) == 0:
							if flt(i.local_mp) != -100:
								i.local_pp_after_tax = flt(i.local_sp) - (flt(i.local_sp) * (flt(i.local_mp) / 100))
								i.new_purchase_price = flt(i.local_pp_after_tax) / (1 + local_tax_decimal)
							else:
								i.local_pp_after_tax = 0
								i.new_purchase_price = 0
						else:
							i.local_pp_after_tax = flt(i.local_sp)
							i.new_purchase_price = flt(i.local_sp) / (1 + local_tax_decimal)
					else:
						i.local_sp = 0
						i.local_sp_after_tax = 0
						i.new_purchase_price = flt(i.new_purchase_price or 0)
						i.local_pp_after_tax = flt(i.new_purchase_price) * (1 + local_tax_decimal)
					i.free_pp_after_tax = flt(i.new_purchase_price) * (1 + free_tax_decimal)
					
					if flt(i.free_mp) or flt(i.free_mp) == 0:
						if flt(i.free_mp) != -100:
							i.free_sp = flt(i.free_pp_after_tax) / (1 - flt(i.free_mp) / 100)
						else:
							i.free_sp = 0
					else:
						i.free_sp = flt(i.free_pp_after_tax)
					
					if flt(i.free_sp):
						i.free_sp_after_tax = flt(i.free_sp) * (1 + free_tax_decimal)
					else:
						i.free_sp_after_tax = 0
				else:
					i.local_pp_after_tax = flt(i.new_purchase_price) * (1 + local_tax_decimal)
					i.free_pp_after_tax = flt(i.new_purchase_price) * (1 + free_tax_decimal)
					if flt(i.local_mp) or flt(i.local_mp) == 0:
						i.local_sp = flt(i.local_pp_after_tax) * (1 + flt(i.local_mp) / 100)
					else:
						i.local_sp = flt(i.local_pp_after_tax)
					if flt(i.free_mp) or flt(i.free_mp) == 0:
						i.free_sp = flt(i.free_pp_after_tax) * (1 + flt(i.free_mp) / 100)
					else:
						i.free_sp = flt(i.free_pp_after_tax)
					
					i.local_sp_after_tax = flt(i.local_sp) * (1 + local_tax_decimal)
					i.free_sp_after_tax = flt(i.free_sp) * (1 + free_tax_decimal)
				if self.pricing_type == "Buying Price Basis":
					if flt(i.local_pp_after_tax) > 0:
						i.local_mp = flt(((flt(i.local_sp or 0) - flt(i.local_pp_after_tax)) / flt(i.local_pp_after_tax)) * 100 , 3)
					else:
						if flt(i.local_sp) > 0:
							i.local_mp = 100
						else:
							i.local_mp = 0
					
					if flt(i.free_pp_after_tax) > 0:
						i.free_mp = flt(((flt(i.free_sp or 0) - flt(i.free_pp_after_tax)) / flt(i.free_pp_after_tax)) * 100 , 3)
					else:
						if flt(i.free_sp) > 0:
							i.free_mp = 100
						else:
							i.free_mp = 0
				else:
					if flt(i.local_sp) > 0:
						i.local_mp = flt(((flt(i.local_sp or 0) - flt(i.local_pp_after_tax)) / flt(i.local_sp)) * 100 , 3)
					else:
						if flt(i.local_pp_after_tax) > 0:
							i.local_mp = -100 
						else:
							i.local_mp = 0
					
					if flt(i.free_sp) > 0:
						i.free_mp = flt(((flt(i.free_sp or 0) - flt(i.free_pp_after_tax)) / flt(i.free_sp)) * 100 , 3)
					else:
						if flt(i.free_pp_after_tax) > 0:
							i.free_mp = -100 
						else:
							i.free_mp = 0
				
				new_total_quantity += flt(i.new_quantity or 0)
				local_sa += flt(i.new_quantity or 0) * flt(i.local_sp or 0)
				free_sa += flt(i.new_quantity or 0) * flt(i.free_sp or 0)
				new_purchase_amount += flt(i.new_quantity or 0) * flt(i.new_purchase_price or 0)
			self.new_total_quantity = new_total_quantity
			self.local_sa = local_sa
			self.free_sa = free_sa
			self.new_purchase_amount = new_purchase_amount
	
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
		buying , selling  , selling_free_zone = get_standard_price_list_b_s_sfz()
		for i in self.items:
			if i.new_purchase_price > i.local_sp or i.new_purchase_price > i.free_sp:
				frappe.throw(_("Row #{0}: Rate cannot be greater than Selling Price for item {1}").format(i.idx, i.item_code))
			ip_buy = frappe.new_doc("Item Price")
			ip_buy.item_code = i.item_code
			ip_buy.price_list = buying
			ip_buy.price_list_rate = i.new_purchase_price
			ip_buy.valid_from = self.posting_date
			ip_buy.custom_supplier_agreement = self.blanket_order
			ip_buy.custom_pricing_sheet = self.name
			ip_buy.insert(ignore_permissions=True)
			ip_sell = frappe.new_doc("Item Price")
			ip_sell.item_code = i.item_code
			ip_sell.price_list = selling
			ip_sell.price_list_rate = i.local_sp
			ip_sell.valid_from = self.posting_date
			ip_sell.custom_supplier_agreement = self.blanket_order
			ip_sell.custom_pricing_sheet = self.name
			ip_sell.insert(ignore_permissions=True)
			ip_sell_free_zone = frappe.new_doc("Item Price")
			ip_sell_free_zone.item_code = i.item_code
			ip_sell_free_zone.price_list = selling_free_zone
			ip_sell_free_zone.price_list_rate = i.free_sp
			ip_sell_free_zone.valid_from = self.posting_date
			ip_sell_free_zone.custom_supplier_agreement = self.blanket_order
			ip_sell_free_zone.custom_pricing_sheet = self.name
			ip_sell_free_zone.insert(ignore_permissions=True)
   
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
             				`tabActive File Income` 
         				WHERE 
             				posting_date = t.posting_date
                 	)
    			) AS last_sync_datetime
			FROM 
   				`tabActive File Income` t
			WHERE 
   				posting_date = (
    				SELECT 
        				MAX(posting_date) 
    				FROM 
        				`tabActive File Income`
				)
			LIMIT 
   				1""")
		if self.docstatus == 0:
			if sql and sql[0][0]:
				return datetime.strptime(str(sql[0][0]), "%Y-%m-%d %H:%M:%S.%f")
		return None

	def autoname(self):
		last = frappe.db.get_value("Pricing Sheet", {'blanket_order': self.blanket_order}, "name", order_by="creation DESC")
		if last and last.startswith(f"{self.blanket_order}/"):
			try:
				last_number = int(last.split("/")[-1])
			except:
				last_number = 0
		else:
			last_number = 0
		new_number = last_number + 1
		self.name = f"{self.blanket_order}/{new_number}"
	def create_pos_item(self):
		sa_doc = get_doc("Blanket Order", self.blanket_order)
		if sa_doc.docstatus == 1 and sa_doc.custom_status == "Active":
			items_local_zone = []
			items_free_zone = []
			supplier_code = db.get_value("Supplier", self.supplier, "custom_supplier_code")
			for item in self.items:
				is_disabled = db.get_value("Item", item.item_code, "disabled")
				is_disabled_sales = db.get_value("Item", item.item_code, "is_sales_item")
				if is_disabled == 1 or is_disabled_sales == 0:
					is_disabled = 1
				else:
					is_disabled = 0
				items_local_zone.append({
					"ITEMNO": item.item_code,
					"BARCODE": get_item_barcode(item.item_code),
					"ITEMSHORTNAME": item.item_name,
					"ITEMTAX":item.local_tax_rate,
					"ITEMPRICE": item.local_sp,
					"ITEMSTOP": is_disabled,
					"TRN_TYPE_PRICE": 1
				})
				items_free_zone.append({
					"ITEMNO": item.item_code,
					"BARCODE": get_item_barcode(item.item_code),
					"ITEMSHORTNAME": item.item_name,
					"ITEMTAX":item.free_tax_rate,
					"ITEMPRICE": item.free_sp,
					"ITEMSTOP": is_disabled,
					"TRN_TYPE_PRICE": 8
				})
				
			payload_local_zone = {
				"AGREEMENT_NO": self.blanket_order,
				"ITEMS": items_local_zone,
				"COMP_CODE": supplier_code if supplier_code else "",
				"AGR_STDATE": sa_doc.from_date,
				"AGR_ENDATE": sa_doc.to_date,
			}
			payload_free_zone = {
				"AGREEMENT_NO": self.blanket_order,
				"ITEMS": items_free_zone,
				"COMP_CODE": supplier_code if supplier_code else "",
				"AGR_STDATE": sa_doc.from_date,
				"AGR_ENDATE": sa_doc.to_date,
			}
			insert_pos_item(payload_local_zone, payload_free_zone)