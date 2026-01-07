// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Terms Template", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Supplier Agreement Other Terms", {
    tcs_terms(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.tcs_terms) {
            row.terms = "";
            frm.refresh_field("terms");
            return;
        }
        frappe.db.get_value("Terms and Conditions", row.tcs_terms, "terms")
            .then(r => {
                row.terms = r.message?.terms || "";
                frm.refresh_field("terms");
            });
    }
});