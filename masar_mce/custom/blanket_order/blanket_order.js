frappe.ui.form.on("Blanket Order", {
    onload: function(frm) {
        filterBySupplier(frm);
        CreateRequiredInspectionButton(frm);
        CloseandHoldButton(frm);
        hide_buttons(frm);
    },
    refresh:  function(frm) {
        filterBySupplier(frm);
        CreateRequiredInspectionButton(frm);
        CloseandHoldButton(frm);
        hide_buttons(frm);
    },
    setup:  function(frm) {
        filterBySupplier(frm);
        CreateRequiredInspectionButton(frm);
        CloseandHoldButton(frm);
        hide_buttons(frm);
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
    }, 
    custom_pricing_type(frm) {
        frm.refresh_field("items");
        CalculateSellingPrice(frm, cdt, cdn);
        CalculateMarkupPercentage(frm, cdt, cdn);
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
        CalculateSellingPrice(frm, cdt, cdn);
        CalculateMarkupPercentage(frm, cdt, cdn);
    },
    items_remove(frm) {
        update_total(frm);
    },
    custom_markup_percentage(frm, cdt, cdn) {
        CalculateSellingPrice(frm, cdt, cdn);
    },
    custom_selling_price(frm, cdt, cdn) {
        CalculateMarkupPercentage(frm, cdt, cdn);
    }
});
function CalculateAmount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.custom_amount = (flt(row.qty) || 0) * (flt(row.rate) || 0);
    frm.refresh_field("items");

    update_total(frm);
}
function CalculateSellingPrice(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (frm.doc.custom_pricing_type === 'Buying Price Basis') {
        if (flt(row.rate) && flt(row.custom_markup_percentage)) {
            row.custom_selling_price = flt(row.rate) + (flt(row.rate) * flt(row.custom_markup_percentage) / 100);
        } else {
            row.custom_selling_price = 0;
        }
        frm.refresh_field("items");
    }
}
function CalculateMarkupPercentage(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (frm.doc.custom_pricing_type === 'Selling Price Basis') {
        if (flt(row.rate) && flt(row.custom_selling_price)) {
            row.custom_markup_percentage = ((flt(row.custom_selling_price) - flt(row.rate)) / flt(row.rate)) * 100;
        } else {
            row.custom_markup_percentage = 0;
        }
        frm.refresh_field("items");
    }
}
function update_total(frm) {
    let total = 0;
    (frm.doc.items || []).forEach(d => {
        total += flt(d.custom_amount);
    });
    frm.set_value("custom_agreement_total", total);
}
frappe.form.link_formatters['Item'] = function(value, doc) {
    if(doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    } else {
        return value;
    }
};
function hide_buttons(frm) {
    setTimeout(() => {
        if(frm.doc.custom_status != 'Active') {
            cur_frm.page.remove_inner_button(__('Purchase Order'), __('Create'));
        }
    }, 100);
}
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
function CloseandHoldButton(frm) {
    if (frm.doc.docstatus === 1 && frm.doc.custom_status === 'Active' ) {
        frm.add_custom_button(__('Close'), function () {
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: frm.doctype,
                    name: frm.doc.name,
                    fieldname: 'custom_status',
                    value: 'Closed'
                },
                callback: function(r) {
                    if (!r.exc) {
                        frm.doc.custom_status = 'Closed';
                        frm.refresh_fields();
                        frm.reload_doc();
                        frappe.show_alert({
                            message: __('Status updated to Closed'),
                            indicator: 'green'
                        });
                    }
                }
            });
        }, __('Status'));

        frm.add_custom_button(__('Hold'), function () {
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: frm.doctype,
                    name: frm.doc.name,
                    fieldname: 'custom_status',
                    value: 'Hold'
                },
                callback: function(r) {
                    if (!r.exc) {
                        frm.doc.custom_status = 'Hold';
                        frm.refresh_fields();
                        frm.reload_doc();
                        frappe.show_alert({
                            message: __('Status updated to Hold'),
                            indicator: 'green'
                        });
                    }
                }
            });
        }, __('Status'));
    }

    if (frm.doc.docstatus === 1 && frm.doc.custom_status === 'Hold') {
        frm.add_custom_button(__('Resume'), function () {
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: frm.doctype,
                    name: frm.doc.name,
                    fieldname: 'custom_status',
                    value: 'Active'
                },
                callback: function(r) {
                    if (!r.exc) {
                        frm.doc.custom_status = 'Active';
                        frm.refresh_fields();
                        frm.reload_doc();
                        frappe.show_alert({
                            message: __('Status updated to Active'),
                            indicator: 'green'
                        });
                    }
                }
            });
        }, __('Status'));
    }
}
