# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import throw, bold, get_doc, get_value
from frappe.utils.safe_exec import safe_eval
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController

class PenaltyEntry(AccountsController):
    def validate(self): 
        self.check_penalties()
    
    def on_submit(self): 
        self.create_gl_entry()
    def on_cancel(self):
        self.cancel_gl_entry()
        self.cancel_payment_ledger_entry()

    @frappe.whitelist()
    def get_penalties_from_supplier_agreement(self):
        if not self.supplier_agreement:
            return 
        res = frappe.db.sql("""
                SELECT penalty as name, penalty_type, account, amount, formula
                FROM `tabSupplier Agreement Penalty Details`
                WHERE parent = %s
        """, (self.supplier_agreement), as_dict=True)
        return res
    
    def check_penalties(self):
        sa_penalties = [i.name for i in 
                        frappe.db.sql(
                            f"""
                            SELECT penalty as name 
                            FROM `tabSupplier Agreement Penalty Details`
                            WHERE parent = '{self.supplier_agreement}'
                            """
                        , as_dict=True) 
        ]
        for r in self.penalties: 
            if r.penalty not in sa_penalties:
                throw(f"Row{bold(r.idx)}: Penalty {bold(r.penalty)} Not exist in Supplier Agreement {bold(self.supplier_agreement)}")
                
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
            if row.penalty_type == "Fixed Value":
                amount = row.amount
            else:
                document = get_value('Penalty', row.penalty, 'formula_doctype')
                if document is None:
                    frappe.throw(f'Row {row.idx}: Penalty {row.penalty} need update in formula.')
                if document == 'Purchase Receipt' and self.purchase_receipt is None:
                    frappe.throw("Purchase Receipt needed for formula.")
                try:
                    doc = get_doc(document, self.supplier_agreement if document == 'Blanket Order' else self.purchase_receipt).as_dict()
                    amount = safe_eval(row.formula, None, doc)
                    if amount is None:
                        frappe.throw(f"Formula returned None for penalty '{row.penalty}'. Please set a valid value.")
                except Exception as e:
                    frappe.throw(f"Error in formula for penalty '{row.penalty}': {str(e)}")

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