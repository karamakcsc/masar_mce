// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Penalty Entry", {
    refresh: function(frm) {
        fetch_penalties(frm);
        view_accounting_ledger(frm);
        filter_penalties(frm);
    },
    supplier_agreement: function(frm) {
        filter_penalties(frm);
    },
    onload: function(frm) {
        filter_penalties(frm);
    }, 
    setup: function(frm) {
        filter_penalties(frm);
    }
});


function fetch_penalties(frm) {
    if (frm.doc.docstatus === 0 ){
        frm.add_custom_button(__("Get Penalties"), function () {
            frappe.call({
                method: "get_penalties_from_supplier_agreement",
                doc: frm.doc,
                callback: function (r) {
                    if (r.message) {
                        frm.clear_table("penalties");
                        r.message.forEach(function (d) {
                            let row = frm.add_child("penalties");
                            frappe.model.set_value(row.doctype, row.name, "penalty", d.name);
                            frappe.model.set_value(row.doctype, row.name, "penalty_type", d.penalty_type);
                            frappe.model.set_value(row.doctype, row.name, "account", d.account);
                            frappe.model.set_value(row.doctype, row.name, "amount", d.amount);
                            frappe.model.set_value(row.doctype, row.name, "formula", d.formula);
                        });
                        frm.refresh_field("penalties");
                    }
                }
            });
        });
    }
}

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

function filter_penalties(frm) {
    const grid = frm.fields_dict.penalties.grid;
    const penalty_field = grid.get_field("penalty");
    if (!penalty_field.hasOwnProperty('original_get_query')) {
        penalty_field.original_get_query = penalty_field.get_query;
    }
    
    penalty_field.get_query = function() {
        if (frm.doc.docstatus === 0 && frm.doc.supplier_agreement) {
            return {
                query: "masar_mce.masar_mce.doctype.penalty_entry.test_penalty_entry.get_pens_from_blanket_order",
                filters: {
                    blanket_order: frm.doc.supplier_agreement
                }
            };
        }
        return {};
    };
}