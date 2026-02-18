
import frappe 
from frappe.utils import flt 
from frappe import _


def validate_against_blanket_order(order_doc):
	if order_doc.doctype in ("Sales Order", "Purchase Order"):
		order_data = {}

		for item in order_doc.get("items"):
			if item.against_blanket_order and item.blanket_order:
				if item.blanket_order in order_data:
					if item.item_code in order_data[item.blanket_order]:
						order_data[item.blanket_order][item.item_code] += item.qty
					else:
						order_data[item.blanket_order][item.item_code] = item.qty
				else:
					order_data[item.blanket_order] = {item.item_code: item.qty}

		if order_data:
			allowance = flt(
				frappe.db.get_single_value(
					"Selling Settings" if order_doc.doctype == "Sales Order" else "Buying Settings",
					"blanket_order_allowance",
				)
			)
			for bo_name, item_data in order_data.items():
				bo_doc = frappe.get_doc("Blanket Order", bo_name)
				for item in bo_doc.get("items"):
					if item.item_code in item_data:
						remaining_qty = item.qty 
						allowed_qty = remaining_qty + (remaining_qty * (allowance / 100)) - item.ordered_qty
						if item.qty and allowed_qty < item_data[item.item_code]:
							frappe.throw(
								_(
									"Item {0} cannot be ordered more than {1} against Blanket Order {2}."
								).format(item.item_code, allowed_qty, bo_name)
							)