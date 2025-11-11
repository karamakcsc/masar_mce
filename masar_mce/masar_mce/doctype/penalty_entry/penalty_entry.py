# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import throw, bold, get_doc, get_value
from frappe.utils.safe_exec import safe_eval
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController
from frappe.utils import flt, date_diff, getdate

class PenaltyEntry(AccountsController):
    def validate(self): 
        self.calculate_amount_values()
    
    def on_submit(self): 
        self.create_gl_entry()
    def on_cancel(self):
        self.cancel_gl_entry()
        self.cancel_payment_ledger_entry()

    def calculate_amount_values(self):
        for row in self.penalties:
            penalty_doc = frappe.get_doc('Penalty', row.penalty)
            if row.penalty_type == "Fixed Value":
                p_amount = frappe.db.get_value('Penalty' , row.penalty , 'penalty_amount')
            else:
                p_amount  = flt(self.pr_total) *  flt(get_value('Penalty', row.penalty, 'penalty_percentage')) / 100 
                
            if penalty_doc.based_on_days:
                pr_doc = frappe.get_doc('Purchase Receipt' , self.purchase_receipt)
                if pr_doc.posting_date > pr_doc.custom_delivery_date:
                    extra_days = date_diff(getdate(pr_doc.posting_date), getdate(pr_doc.custom_delivery_date))
                    if extra_days > 0:
                        p_amount = p_amount * extra_days
                else: 
                    p_amount = 0
            row.amount = p_amount
    
                
    def create_gl_entry(self): 
        def get_debit_account():
            account = None
            if self.supplier is None: 
                return None 
            supp_doc = frappe.get_doc('Supplier', self.supplier)
            for i in supp_doc.accounts: 
                if i.company == self.company: 
                    account = i.account
            if account: 
                return account
            if supp_doc.supplier_group is not None: 
                group_doc = frappe.get_doc('Supplier Group', supp_doc.supplier_group)
                for i in group_doc.accounts: 
                    if i.company == self.company: 
                        account = i.account
                if account: 
                    return account
            return frappe.get_value('Company', self.company, 'default_payable_account')

        debit_account = get_debit_account()
        if not debit_account:
            frappe.throw(
                f"No payable account found for Supplier {self.supplier} or Company {self.company}"
            )
        gl_entries = []
        for row in self.penalties:
            penalty_doc = frappe.get_doc('Penalty', row.penalty)
            if row.penalty_type == "Fixed Value":
                amount = frappe.db.get_value('Penalty' , row.penalty , 'penalty_amount')
            else:
                amount  = flt(self.pr_total) *  flt(get_value('Penalty', row.penalty, 'penalty_percentage')) / 100 
                
            if penalty_doc.based_on_days:
                pr_doc = frappe.get_doc('Purchase Receipt' , self.purchase_receipt)
                warehouse = frappe.get_doc('Warehouse', pr_doc.set_warehouse)
                allowed_days = warehouse.custom_number_of_days
                if pr_doc.posting_date > pr_doc.custom_request_date:
                    extra_days = date_diff(getdate(pr_doc.posting_date), getdate(pr_doc.custom_request_date))
                    if extra_days > allowed_days:
                        amount = amount * extra_days
                else: 
                    amount = 0

            if not amount or amount == 0:
                continue
            gl_entries.append( 
                self.get_gl_dict({
                "account": debit_account,
                "against" : row.account,
                "debit": amount,
                "debit_in_account_currency": amount,
                "party_type" : "Supplier",
                "party": self.supplier,
                "cost_center": self.get_cost_center(),
                "remarks": f"Penalty - {row.penalty}",
            }))
            gl_entries.append(
                self.get_gl_dict({
                "account": row.account,
                "credit": amount,
                "credit_in_account_currency": amount,
                "against": debit_account,
                "cost_center": self.get_cost_center(),
                "remarks": f"Penalty - {row.penalty}",
            }))
        
        if gl_entries:
            make_gl_entries(gl_map = gl_entries , merge_entries= False)
    
    def get_cost_center(self):
        """Get cost center from company or other sources"""
        cost_center = frappe.get_cached_value('Company', self.company, 'cost_center')
        if not cost_center:
            frappe.throw(f"Please set default cost center for company {self.company}")
        return cost_center
    
    def cancel_gl_entry(self):
        gl_entry_names = frappe.db.sql_list("""
            SELECT name FROM `tabGL Entry`
            WHERE voucher_type = %s AND voucher_no = %s
        """, (self.doctype, self.name))
        if gl_entry_names:
            frappe.db.sql("DELETE FROM `tabGL Entry` WHERE name IN %s", (gl_entry_names,))
            frappe.db.commit()
            

    def cancel_payment_ledger_entry(self): 
        ple_names = frappe.db.sql_list("""
            SELECT name FROM `tabPayment Ledger Entry`
            WHERE voucher_type = %s AND voucher_no = %s
        """, (self.doctype, self.name))
        if ple_names:
            frappe.db.sql("DELETE FROM `tabPayment Ledger Entry` WHERE name IN %s", (ple_names,))
            frappe.db.commit()