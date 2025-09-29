import frappe 
from frappe.utils import flt

def validate(self , method):
    calculate_amounts_and_total(self)
    if self.is_new():
        get_default_penalty(self)

@frappe.whitelist()
def get_items_by_supplier(doctype, txt, searchfield, start, page_len, filters):
    supplier = filters.get("supplier")
    return frappe.db.sql(f"""
        SELECT DISTINCT parent as name 
        FROM `tabItem Supplier`
        WHERE supplier = '{supplier}'
        ORDER BY parent
    """)

def calculate_amounts_and_total(self):
    total , total_qty  = 0  , 0 
    for i in self.items:
        amount = flt(i.qty) * flt(i.rate)
        i.custom_amount = amount
        total += amount
        total_qty += i.qty
    self.custom_total_quantity = total_qty
    self.custom_total = total
    
def get_default_penalty(self):
    all_penalty = frappe.db.sql(
        """
        SELECT name, penalty_type, account, penalty_amount, penalty_formula
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
            'account': p.account,
            'penalty_amount': p.penalty_amount,
            'penalty_formula': p.penalty_formula
        })
