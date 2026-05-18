import frappe 
from frappe import _
from frappe.utils import flt
from erpnext.accounts.general_ledger import make_gl_entries




def validate(self , method ):
    validate_item_markets_for_stock_entry(self)
    if self.stock_entry_type in ["Bonus Receipt" ,'سند استلام البونص']:
        validate_bonus_receipt(self)
def validate_item_markets_for_stock_entry(self):
    if not self.items:
        return
    if self.purpose not in ["Material Receipt", "Material Transfer"]:
        return
    for row in self.items:
        item_code = row.item_code
        if self.purpose == "Material Receipt":
            warehouse = row.t_warehouse or self.to_warehouse
        elif self.purpose == "Material Transfer":
            warehouse = row.t_warehouse
        else:
            warehouse = None
        if not warehouse:
            
            msg= _("Row #{0}: Target Warehouse is required for item {1}").format(row.idx, item_code)
            if self.docstatus == 1 :
                frappe.throw(msg)
            else:
                frappe.msgprint(msg)
            
        wh_type = frappe.db.get_value("Warehouse", warehouse, "warehouse_type") if warehouse else None
        if wh_type  in ("Store", "سوق"):
            has_restriction = frappe.db.exists(
                "Item Markets",
                {
                    "item_code": item_code,
                    "disabled": 0
                }
            )
            if has_restriction:
                allowed = frappe.db.exists(
                    "Item Markets",
                    {
                        "item_code": item_code,
                        "warehouse": warehouse,
                        "disabled": 0
                    }
                )
                if not allowed:
                    msg = _(
                            "Row #{0}: Item <b>{1}</b> is not allowed in Warehouse <b>{2}</b> as per Item Markets."
                        ).format(row.idx, item_code, warehouse)
                    if self.docstatus == 1 :
                        frappe.throw(msg)
                    else:
                        frappe.msgprint(msg)


def on_submit(self , method):
    if self.stock_entry_type  in ['Material Receipt for Inspection' , 'سند إستلام لفحص الجودة' ]:
        check_agreement_items(self)
        create_quality_inspection(self)
    if self.stock_entry_type  in ['Return to Supplier' , 'إرجاع إلى المورد' ]:
        validate_party_specific_item(self)
        make_gl_entry(self)    
    
        
def validate_bonus_receipt(self):
    if frappe.db.get_value(
        "Warehouse",
        self.to_warehouse,
        "warehouse_type"
    ) not in ["Bouns", "بونص"]:
        frappe.throw(
            _("For Bonus Type, the Target Warehouse must be a Bonus Warehouse Type.")
        )
    for i in self.items:
        if hasattr(i , "to_bonus_warehouse") :
            i.to_bonus_warehouse = self.custom_bonus_warehouse
        i.allow_zero_valuation_rate = 1 
        i.basic_rate = 0 
        i.valuation_rate = 0    
            
        
def create_quality_inspection(self):
    exist_items = list()
    for i in self.items:
        if i.item_code in exist_items:
            continue
        exist_items.append(i.item_code)
        frappe.new_doc("Quality Inspection").update({
            "inspection_type":"Incoming",
            "reference_type":"Stock Entry",
            "custom_supplier_agreement": self.custom_supplier_agreement,
            "reference_name":self.name,
            "item_code":i.item_code,
            "inspected_by" : frappe.session.user,
            "sample_size": i.qty
        }).insert(ignore_permissions=True)
def get_income_account(item_code = None):
    if item_code: 
        item_doc = frappe.get_doc('Item' , item_code)
        for account in item_doc.item_defaults:
            if account.income_account: 
                return account.income_account
        if item_doc.item_group:
            group_doc = frappe.get_doc('Item Group' , item_doc.item_group)
            if group_doc.item_group_defaults:
                for acc_group in group_doc.item_group_defaults:
                    if acc_group.income_account: 
                        return acc_group.income_account ##        
    return None

def get_supplier_account(self):
    supplier_doc = frappe.get_doc('Supplier' , self.custom_supplier)
    account = None
    for acc in  supplier_doc.accounts:
        if acc.company == self.company: 
            account = acc.account
    if account is not None: 
        return account
    if supplier_doc.supplier_group is not None: 
        group_doc = frappe.get_doc('Supplier Group', supplier_doc.supplier_group)
        for acc_g in group_doc.accounts: 
            if acc_g.company == self.company:
                account  = acc_g.account
    if account is not None: 
        return account
    company_doc = frappe.get_doc('Company' , self.company)
    if company_doc.default_payable_account:
        return company_doc.default_payable_account
    return None
@frappe.whitelist()
def get_items_from_party_specific_item(doctype, txt, searchfield, start, page_len, filters):
    party = filters.get("party")
    party_type = filters.get("party_type", "Supplier")

    return frappe.db.sql("""
        SELECT 
            i.name, 
            i.item_name
        FROM `tabItem` i
        INNER JOIN `tabParty Specific Item` psi
            ON psi.based_on_value = i.name AND psi.restrict_based_on = 'Item'
        WHERE
            psi.party_type = %s
            AND psi.party = %s
            AND i.disabled = 0
            AND (i.name LIKE %s OR i.item_name LIKE %s)
        ORDER BY i.name
        LIMIT %s OFFSET %s
    """, (
        party_type,
        party,
        f"%{txt}%",
        f"%{txt}%",
        page_len,
        start
    ))
    
      
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_from_blanket_order(doctype, txt, searchfield, start, page_len, filters):
    blanket_order = filters.get("blanket_order")
    if not blanket_order:
        return []

    query = """
        SELECT DISTINCT 
            boi.item_code AS name,
            item.item_name
        FROM `tabBlanket Order Item` boi
        INNER JOIN `tabItem` item ON boi.item_code = item.name
        WHERE boi.parent = %(blanket_order)s
        AND (boi.item_code LIKE %(txt)s OR item.item_name LIKE %(txt)s)
        ORDER BY boi.item_code
        LIMIT %(start)s, %(page_len)s
    """

    return frappe.db.sql(query, {
        "blanket_order": blanket_order,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })

def validate_party_specific_item(self):
    for i in self.items:
        if not frappe.db.exists(
            "Party Specific Item",
            {
                "based_on_value": i.item_code,
                "party_type": "Supplier",
                "party": self.custom_supplier
            }
        ):
            frappe.throw(_("Item {0} is not allowed for Supplier {1}").format(i.item_code, self.custom_supplier))
    return True
 
def check_agreement_items(self):
    if self.stock_entry_type not in ['Material Receipt for Inspection' , 'سند إستلام لفحص الجودة' ]:
        return

    if not self.custom_supplier_agreement:
        frappe.throw(_("Select Supplier Agreement."))

    allowed_items = frappe.get_all(
        "Blanket Order Item",
        filters={"parent": self.custom_supplier_agreement},
        pluck="item_code"
    )

    for row in self.items:
        if row.item_code not in allowed_items:
            frappe.throw(
                _("Item {0} is not in Supplier Agreement: {1}").format(row.item_code, self.custom_supplier_agreement)
            )

            
    for row in self.items:
        sa_row = frappe.db.sql(f"""
            SELECT r.name  , sa.docstatus
            FROM `tabBlanket Order` sa
            INNER JOIN `tabBlanket Order Item` r ON r.parent = sa.name
            WHERE r.item_code = '{row.item_code}'
            AND sa.name = '{self.custom_supplier_agreement}'
        """ , as_dict= True)
        if sa_row and sa_row[0]:
            frappe.db.set_value('Blanket Order Item'  , sa_row[0]['name'] , 'custom_inspection_is_required' , 1)
            frappe.db.set_value('Blanket Order Item'  , sa_row[0]['name'] , 'custom_quality_inspection_quantity' , row.qty)
            
            
            
def make_gl_entry(self): 
    gl_entries = []
    company = self.company
    adj_amount = flt(self.total_outgoing_value)
    stock_adjustment_account = frappe.get_value(
        "Company", self.company, "stock_adjustment_account"
    )
    company_cc = frappe.get_value(
        "Company", company, "cost_center"
    )
    diff = 0
    posting_date = self.posting_date
    supplier_account = get_supplier_account(self)
    if adj_amount > 0:
        gl_entries.append(
            self.get_gl_dict({
            "posting_date": posting_date,
            "account": stock_adjustment_account,
            "credit": adj_amount,
            "debit": 0,
            "voucher_type": self.doctype,
            "voucher_no": self.name,
            "remarks": "Close stock adjustment for Return to Supplier",
            "company": company,
            "cost_center": company_cc
        }))
    for item in self.items:
        income_acc = get_income_account(item.item_code)
        if income_acc is None:
            income_acc = frappe.get_value(
                "Company", self.company, "default_income_account"
            )
        if income_acc:
            cost_zone = frappe.db.get_value('Warehouse', item.s_warehouse, 'custom_cost_zone')
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
                selling_value = flt(price_list_rate[0][0]) * flt(item.qty)
                stock_value = flt(item.amount)
                diff += selling_value - stock_value
                gl_entries.append(
            self.get_gl_dict({
                    "posting_date": posting_date,
                    "account": supplier_account,
                    "debit": selling_value,
                    "credit": 0,
                    "party_type": "Supplier",
                    "party": self.custom_supplier,
                    "voucher_type": self.doctype,
                    "voucher_no": self.name,
                    "remarks": f"Supplier debit for item {item.item_code}",
                    "company": company
                }))
    if diff  > 0:
        gl_entries.append(
            self.get_gl_dict({
                "posting_date": posting_date,
                "account": income_acc,
                "credit": round(diff , 3),
                "debit": 0,
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "remarks": f"Revenue from Return to Supplier ({item.item_code})",
                "company": company,
                "cost_center": company_cc
            }))

    if gl_entries:
        make_gl_entries(
            gl_entries,
            cancel=False,
            update_outstanding="Yes"
        )