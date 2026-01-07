// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Penalty Entry", {
    refresh(frm) {
        view_accounting_ledger(frm);
    },

    purchase_receipt(frm) {
        if (!frm.doc.purchase_receipt) {
            frm.set_value("purchase_request", null);
            frm.set_value("pr_total", 0);
            frm.refresh_fields();
            return;
        };

        frappe.call({
            doc: frm.doc,
            method: "get_request_details",
            callback(r) {
                if (r.message) {
                    frm.set_value("purchase_request", r.message.purchase_request);
                    frm.set_value("pr_total", r.message.pr_total);
                    frm.refresh_fields();
                }
            }
        });
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