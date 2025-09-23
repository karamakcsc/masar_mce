# Copyright (c) 2025, KCSC and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPenaltyEntry(FrappeTestCase):
	pass


@frappe.whitelist()
def get_pens_from_blanket_order(doctype, txt, searchfield, start, page_len, filters):
    blanket_order = filters.get("blanket_order")
    return frappe.db.sql(f"""
        SELECT DISTINCT penalty as name
        FROM `tabSupplier Agreement Penalty Details`
        WHERE parent = '{blanket_order}'
    """)
    
