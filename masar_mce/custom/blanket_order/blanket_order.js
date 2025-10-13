frappe.ui.form.on("Blanket Order", {
    onload: function(frm) {
        filterBySupplier(frm);
        CreateRequiredInspectionButton(frm);
    },
    refresh:  function(frm) {
        filterBySupplier(frm);
        CreateRequiredInspectionButton(frm);
    },
    setup:  function(frm) {
        filterBySupplier(frm);
        CreateRequiredInspectionButton(frm);
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
    const grid = frm.fields_dict.items.grid;
    const item_code_field = grid.get_field("item_code");
    if (!item_code_field) return;
    if (!item_code_field.hasOwnProperty('original_get_query')) {
        item_code_field.original_get_query = item_code_field.get_query;
    }
    item_code_field.get_query = function() {
        const filters = {};
        if (frm.doc.supplier) {
            filters.supplier = frm.doc.supplier;
        }
        
        return {
            query: "masar_mce.custom.blanket_order.blanket_order.get_items_by_supplier",
            filters: filters
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
frappe.form.link_formatters['Item'] = function(value, doc) {
    if(doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    } else {
        return value;
    }
};
function CreateRequiredInspectionButton(frm) {
    if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frm.add_custom_button(__('Material Receipt for Inspection'), function() {
                frappe.model.open_mapped_doc({
                    method: 'masar_mce.custom.blanket_order.blanket_order.create_stock_entry_for_inspection',
                    source_name: frm.doc.name
                });
            }, __('Create'));
        }
}