frappe.ui.form.on("Blanket Order", {
    onload(frm) {
        init_form(frm);
        if (frm.doc.from_date && !frm.doc.to_date) {
            let to_date = frappe.datetime.add_days(frm.doc.from_date, 364);
            frm.set_value("to_date", to_date);
        }
    },
    refresh(frm) {
        init_form(frm);
    },
    setup(frm) {
        init_form(frm);
    },
    custom_tcs_terms(frm) {
        if (!frm.doc.custom_tcs_terms) {
            frm.set_value("custom_special_terms", "");
            return;
        }
        frappe.db.get_value("Terms and Conditions", frm.doc.custom_tcs_terms, "terms")
            .then(r => {
                frm.set_value("custom_special_terms", r.message?.terms || "");
            });
    },
    custom_pricing_type(frm) {
        setupFieldReadOnly(frm);
        if (frm.doc.items) {
            frm.doc.items.forEach(row => {
                const cdt = "Blanket Order Item";
                const cdn = row.name;                
                getTaxRate(row.item_code, tax => {
                    if (frm.doc.custom_pricing_type === "Buying Price Basis") {
                        if (flt(row.rate)) {
                            row.custom_purchase_price_after_tax = flt(row.rate) * (1 + flt(tax));
                        }
                        if (flt(row.custom_markup_percentage)) {
                            const selling_before_tax = flt(row.custom_purchase_price_after_tax) * (1 + flt(row.custom_markup_percentage) / 100);
                            row.custom_selling_price = selling_before_tax;
                            row.custom_selling_price_after_tax = selling_before_tax * (1 + flt(tax));
                        }
                    } else {
                        if (flt(row.custom_selling_price_after_tax)) {
                            const selling_before_tax = flt(row.custom_selling_price_after_tax) / (1 + flt(tax));
                            row.custom_selling_price = selling_before_tax;
                            
                            if (flt(row.custom_markup_percentage)) {
                                row.custom_purchase_price_after_tax = selling_before_tax / (1 + flt(row.custom_markup_percentage) / 100);
                                row.rate = row.custom_purchase_price_after_tax / (1 + flt(tax));
                            }
                        }
                    }
                    refresh(frm, cdt);
                });
            });
        }
    },
    custom_terms_template(frm) {
    if (!frm.doc.custom_terms_template) {
        frm.clear_table("custom_other_terms");
        frm.refresh_field("custom_other_terms");
        return;
    }
    frappe.db.get_doc("Terms Template", frm.doc.custom_terms_template)
        .then(doc => {
            frm.clear_table("custom_other_terms");
            (doc.terms || []).forEach(row => {
                let new_row = frm.add_child("custom_other_terms");
                new_row.tcs_terms = row.tcs_terms;
                new_row.terms = row.terms;
            });
            frm.refresh_field("custom_other_terms");
        });
    },
    from_date(frm) {
        if (frm.doc.from_date && !frm.doc.to_date) {
            let to_date = frappe.datetime.add_days(frm.doc.from_date, 365);
            frm.set_value("to_date", to_date);
        }
    },
    supplier(frm) {
        if (frm.doc.supplier) {
            frm.set_value("custom_title", `اتفاقية: ${frm.doc.supplier}`);
        }
    }
});

frappe.ui.form.on("Blanket Order Item", {
    rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        getTaxRate(row.item_code, tax => {
            row.custom_purchase_price_after_tax = flt(row.rate) * (1 + flt(tax));

            if (frm.doc.custom_pricing_type === "Buying Price Basis") {
                if (flt(row.custom_markup_percentage) >= 0) {
                    const selling_before_tax = flt(row.custom_purchase_price_after_tax) * (1 + flt(row.custom_markup_percentage) / 100);
                    row.custom_selling_price = selling_before_tax;
                    row.custom_selling_price_after_tax = selling_before_tax * (1 + flt(tax));
                } else {
                    row.custom_selling_price = flt(row.custom_purchase_price_after_tax);
                    row.custom_selling_price_after_tax = flt(row.custom_purchase_price_after_tax) * (1 + flt(tax));
                }
            } else {
                if (flt(row.custom_selling_price_after_tax)) {
                    const selling_before_tax = flt(row.custom_selling_price_after_tax) / (1 + flt(tax));
                    row.custom_selling_price = selling_before_tax;
                    if (flt(row.custom_purchase_price_after_tax)) {
                        row.custom_markup_percentage = ((flt(row.custom_selling_price) - flt(row.custom_purchase_price_after_tax)) / flt(row.custom_purchase_price_after_tax)) * 100;
                    }
                }
            }
            
            CalculateAmount(frm, cdt, cdn);
            refresh(frm, cdt);
        });
    },

    custom_markup_percentage(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        getTaxRate(row.item_code, tax => {
            if (frm.doc.custom_pricing_type === "Buying Price Basis") {
                if (flt(row.custom_purchase_price_after_tax) && flt(row.custom_markup_percentage)) {
                    const selling_before_tax = flt(row.custom_purchase_price_after_tax) * (1 + flt(row.custom_markup_percentage) / 100);
                    row.custom_selling_price = selling_before_tax;
                    row.custom_selling_price_after_tax = selling_before_tax * (1 + flt(tax));
                }
            } else {
                if (flt(row.custom_selling_price_after_tax) && flt(row.custom_markup_percentage)) {
                    const selling_before_tax = flt(row.custom_selling_price_after_tax) / (1 + flt(tax));
                    row.custom_selling_price = selling_before_tax;
                    row.custom_purchase_price_after_tax = selling_before_tax - (selling_before_tax * flt(row.custom_markup_percentage) / 100);
                    row.rate = row.custom_purchase_price_after_tax / (1 + flt(tax));
                    CalculateAmount(frm, cdt, cdn);
                }
            }
            refresh(frm, cdt);
        });
    },

    // custom_selling_price_after_tax(frm, cdt, cdn) {
    //     const row = locals[cdt][cdn];
    //     getTaxRate(row.item_code, tax => {
    //         const selling_before_tax = flt(row.custom_selling_price_after_tax) / (1 + flt(tax));
    //         row.custom_selling_price = selling_before_tax;
            
    //         if (frm.doc.custom_pricing_type === "Buying Price Basis") {
    //             if (flt(row.custom_purchase_price_after_tax)) {
    //                 row.custom_markup_percentage = ((flt(row.custom_selling_price) - flt(row.custom_purchase_price_after_tax)) / flt(row.custom_purchase_price_after_tax)) * 100;
    //             }
    //         } else {
    //             if (flt(row.custom_markup_percentage)) {
    //                 row.custom_purchase_price_after_tax = flt(row.custom_selling_price) - (flt(row.custom_selling_price) * flt(row.custom_markup_percentage) / 100);
    //                 row.rate = row.custom_purchase_price_after_tax / (1 + flt(tax));
    //                 CalculateAmount(frm, cdt, cdn);
    //             } else {
    //                 row.custom_purchase_price_after_tax = flt(row.custom_selling_price);
    //                 row.rate = row.custom_purchase_price_after_tax / (1 + flt(tax));
    //                 CalculateAmount(frm, cdt, cdn);
    //             }
    //         }
    //         refresh(frm, cdt);
    //     });
    // },

    custom_purchase_price_after_tax(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        getTaxRate(row.item_code, tax => {
            row.rate = flt(row.custom_purchase_price_after_tax) / (1 + flt(tax));
            
            if (frm.doc.custom_pricing_type === "Buying Price Basis") {
                if (flt(row.custom_markup_percentage) >= 0 ) {
                    const selling_before_tax = flt(row.custom_purchase_price_after_tax) * (1 + flt(row.custom_markup_percentage) / 100);
                    row.custom_selling_price = selling_before_tax;
                    row.custom_selling_price_after_tax = selling_before_tax * (1 + flt(tax));
                } else {
                    row.custom_selling_price = flt(row.custom_purchase_price_after_tax);
                    row.custom_selling_price_after_tax = flt(row.custom_purchase_price_after_tax) * (1 + flt(tax));
                }
            } else {
                if (flt(row.custom_selling_price_after_tax)) {
                    const selling_before_tax = flt(row.custom_selling_price_after_tax) / (1 + flt(tax));
                    row.custom_selling_price = selling_before_tax;
                    row.custom_markup_percentage = ((flt(row.custom_selling_price) - flt(row.custom_purchase_price_after_tax)) / flt(row.custom_purchase_price_after_tax)) * 100;
                }
            }       
            CalculateAmount(frm, cdt, cdn);
            refresh(frm, cdt);
        });
    },

    custom_selling_price(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        getTaxRate(row.item_code, tax => {
            row.custom_selling_price_after_tax = flt(row.custom_selling_price) * (1 + flt(tax));
            
            if (frm.doc.custom_pricing_type === "Buying Price Basis") {
                if (flt(row.custom_purchase_price_after_tax)) {
                    row.custom_markup_percentage = ((flt(row.custom_selling_price) - flt(row.custom_purchase_price_after_tax)) / flt(row.custom_purchase_price_after_tax)) * 100;
                }
            } else {
                if (flt(row.custom_markup_percentage) >= 0 ) {
                    row.custom_purchase_price_after_tax = flt(row.custom_selling_price) - (flt(row.custom_selling_price) * flt(row.custom_markup_percentage) / 100);
                    row.rate = row.custom_purchase_price_after_tax / (1 + flt(tax));
                    CalculateAmount(frm, cdt, cdn);
                } else if (flt(row.custom_purchase_price_after_tax)) {
                    row.custom_markup_percentage = ((flt(row.custom_selling_price) - flt(row.custom_purchase_price_after_tax)) / flt(row.custom_purchase_price_after_tax)) * 100;
                }
            }
            refresh(frm, cdt);
        });
    },

    qty(frm, cdt, cdn) {
        CalculateAmount(frm, cdt, cdn);
    },

    items_remove(frm) {
        update_total(frm);
    }
});

function CalculateSellingBeforeTax(row, tax) {
    if (flt(row.custom_selling_price_after_tax)) {
        row.custom_selling_price = flt(row.custom_selling_price_after_tax) / (1 + flt(tax));
    }
}

function CalculateAmount(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    row.custom_amount = flt(row.qty) * flt(row.rate);
    update_total(frm);
}

function update_total(frm) {
    const total = (frm.doc.items || [])
        .reduce((t, d) => t + flt(d.custom_amount), 0);

    frm.set_value("custom_agreement_total", total);
}

function getTaxRate(itemCode, callback) {
    if (!itemCode) {
        callback(0);
        return;
    }
    frappe.call({
        method: "masar_mce.utils.get_tax_for_item",
        args: { item_code: itemCode },
        callback(r) {
            callback(flt(r.message));
        }
    });
}

function refresh(frm, cdt) {
    frm.refresh_field("items");
}

function init_form(frm) {
    filterBySupplier(frm);
    CreateRequiredInspectionButton(frm);
    CloseandHoldButton(frm);
    hide_buttons(frm);
}

function hide_buttons(frm) {
    setTimeout(() => {
        if (frm.doc.custom_status != 'Active') {
            cur_frm.page.remove_inner_button(__('Purchase Order'), __('Create'));
        }
    }, 100);
}

function CreateRequiredInspectionButton(frm) {
    if (frm.doc.docstatus === 0 && !frm.is_new()) {
        frm.add_custom_button(__('Material Receipt for Inspection'), () => {
            frappe.model.open_mapped_doc({
                method: 'masar_mce.custom.blanket_order.blanket_order.create_stock_entry_for_inspection',
                source_name: frm.doc.name
            });
        }, __('Create'));
    }
}

function CloseandHoldButton(frm) {
    if (frm.doc.docstatus !== 1) return;

    if (frm.doc.custom_status === "Active") {
        add_status_button(frm, "Close", "Closed");
        add_status_button(frm, "Hold", "Hold");
    }

    if (frm.doc.custom_status === "Hold") {
        add_status_button(frm, "Resume", "Active");
    }
}

function add_status_button(frm, label, status) {
    frm.add_custom_button(label, () => {
        frappe.call({
            method: "frappe.client.set_value",
            args: {
                doctype: frm.doctype,
                name: frm.doc.name,
                fieldname: "custom_status",
                value: status
            },
            callback() {
                frm.reload_doc();
                frappe.show_alert({
                    message: __("Status updated to " + status),
                    indicator: "green"
                });
            }
        });
    }, __("Status"));
}

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
frappe.ui.form.on("Supplier Agreement Other Terms", {
    tcs_terms(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.tcs_terms) {
            row.terms = "";
            frm.refresh_field("custom_other_terms");
            return;
        }
        frappe.db.get_value("Terms and Conditions", row.tcs_terms, "terms")
            .then(r => {
                row.terms = r.message?.terms || "";
                frm.refresh_field("custom_other_terms");
            });
    }
});