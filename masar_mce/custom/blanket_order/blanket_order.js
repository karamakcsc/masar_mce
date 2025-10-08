frappe.ui.form.on("Blanket Order", {
    onload: function(frm) {
        filterBySupplier(frm);
    },
    refresh:  function(frm) {
        filterBySupplier(frm);
    },
    setup:  function(frm) {
        filterBySupplier(frm);
    },
    custom_tcs_terms(frm) {
       
        if (frm.doc.custom_tcs_terms) {
            frappe.db.get_value("Terms and Conditions", frm.doc.custom_tcs_terms, "terms")
                .then(r => {
                    if (r && r.message.terms) {
                        frm.set_value("custom_special_terms", r.message.terms);
                    } else {
                        frm.set_value("custom_special_terms", "");
                    }
                });
        } else {
            frm.set_value("custom_special_terms", "");
        }
    }
});
function filterBySupplier(frm) {
    frm.fields_dict.items.grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
        return {
            query: "masar_mce.custom.blanket_order.blanket_order.get_items_by_supplier",
            filters: {
                supplier: frm.doc.supplier
            }
        };
    };
}
frappe.ui.form.on("Blanket Order Item", {
    qty(frm, cdt, cdn) {
        CalculateAmount(frm, cdt, cdn);
    },
    rate(frm, cdt, cdn) {
        CalculateAmount(frm, cdt, cdn);
    }, 
    items_remove(frm, cdt, cdn) {
       update_total(frm);
    }
});

function CalculateAmount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.qty && row.rate) {
        row.custom_amount = flt(row.qty) * flt(row.rate);
    } else {
        row.custom_amount = 0;
    }
    frm.refresh_field("items");
    let total = 0;
    (frm.doc.items || []).forEach(d => {
        total += flt(d.custom_amount);
    });

    frm.set_value("custom_agreement_total", total);
}
function update_total(frm) {
    let total = 0;
    (frm.doc.items || []).forEach(d => total += flt(d.custom_amount));
    frm.set_value("custom_agreement_total", total);
}