// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Penalty Entry", {
    refresh: function(frm) {
        view_accounting_ledger(frm);
    },
    supplier_agreement: function(frm) {
    },
    onload: function(frm) {
    }, 
    setup: function(frm) {
    }
});
function view_accounting_ledger(frm) {
    if (frm.doc.docstatus != 0) {
        frm.add_custom_button(__("Accounting Ledger"), function () {
            frappe.set_route("query-report", "General Ledger", {
                voucher_no: frm.doc.name,
                company: frm.doc.company
            });
        }, __("View"));
    }
}