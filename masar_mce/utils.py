import frappe 
from datetime import datetime
def check_expierd_supplier_agrrement():
    date = datetime.now().date()
    active_sa = frappe.db.sql(
        f"""
        SELECT name FROM `tabBlanket Order` tbo 
        WHERE to_date < '{date}'
        AND tbo.docstatus =1 
        AND tbo.custom_status = 'Active'
        """ , as_dcit = True
    )
    for sa in active_sa:
        sa_doc = frappe.get_doc('Blanket Order' . sa.name)
        sa_doc.custom_status = 'Expired'
        sa_doc.save()
    