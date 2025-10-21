import frappe , json
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
from erpnext.buying.doctype.purchase_order.purchase_order import set_missing_values
@frappe.whitelist()
def get_blanket_order_for_item(item_code, supplier):
    if not item_code or not supplier:
        return {}
    result = frappe.db.sql(
        """
        SELECT bo.name AS parent, boi.name AS name , boi.rate as rate
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


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_from_active_blanket_order(doctype, txt, searchfield, start, page_len, filters):
    supplier = filters.get("supplier")
    if not supplier:
        return []
    query = """
        SELECT DISTINCT
            boi.item_code,
            item.item_name
        FROM `tabBlanket Order` bo
        INNER JOIN `tabBlanket Order Item` boi ON bo.name = boi.parent
        INNER JOIN `tabItem` item ON boi.item_code = item.name
        WHERE bo.supplier = %(supplier)s
        AND bo.docstatus = 1
        AND bo.custom_status = 'Active'
        AND item.disabled = 0
        AND (boi.item_code LIKE %(txt)s OR item.item_name LIKE %(txt)s)
        ORDER BY boi.item_code
        LIMIT %(start)s, %(page_len)s
    """
    return frappe.db.sql(query, {
        "supplier": supplier,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })


@frappe.whitelist()
def create_purchase_request_from_purchase_order(source_name, target_doc=None, args=None):
	if args is None:
		args = {}
	if isinstance(args, str):
		args = json.loads(args)

	has_unit_price_items = frappe.db.get_value("Purchase Order", source_name, "has_unit_price_items")

	def is_unit_price_row(source):
		return has_unit_price_items and source.qty == 0

	def update_item(obj, target, source_parent):
		target.custom_request_quantity , target.qty ,obj.qty= flt(obj.qty) if is_unit_price_row(obj) else flt(obj.qty) - flt(obj.received_qty),1,1
		target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.conversion_factor)
		target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
		target.base_amount = (
			(flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate) * flt(source_parent.conversion_rate)
		)

	def select_item(d):
		filtered_items = args.get("filtered_children", [])
		child_filter = d.name in filtered_items if filtered_items else True
		return child_filter

	doc = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Purchase Receipt",
				"field_map": {"supplier_warehouse": "supplier_warehouse"},
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Purchase Order Item": {
				"doctype": "Purchase Receipt Item",
				"field_map": {
					"name": "purchase_order_item",
					"parent": "purchase_order",
					"bom": "bom",
					"material_request": "material_request",
					"material_request_item": "material_request_item",
					"sales_order": "sales_order",
					"sales_order_item": "sales_order_item",
					"wip_composite_asset": "wip_composite_asset",
				},
				"postprocess": update_item,
				"condition": lambda doc: (
					True if is_unit_price_row(doc) else abs(doc.received_qty) < abs(doc.qty)
				)
				and doc.delivered_by_supplier != 1
				and select_item(doc),
			},
			"Purchase Taxes and Charges": {"doctype": "Purchase Taxes and Charges", "reset_value": True},
		},
		target_doc,
		set_missing_values,
	)

	return doc