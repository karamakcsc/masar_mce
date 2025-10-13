frappe.ui.form.on("Purchase Order", {
    setup(frm) {
        FilterItems(frm);
    }, 
    refresh(frm) {
        FilterItems(frm);
    }, 
    onload(frm) {
        FilterItems(frm);
    }, 
    custom_get_all_items(frm) {
        GetAllItemsFromSupplierAgreement(frm);
    },
    custom_supplier_agreement(frm){
        GetTermsandPenalitesFromAgreement(frm);
    }
});

function FilterItems(frm) {
    const grid = frm.fields_dict.items.grid;
    const item_code_field = grid.get_field("item_code");
    if (!item_code_field.hasOwnProperty('original_get_query')) {
        item_code_field.original_get_query = item_code_field.get_query;
    }
    
    item_code_field.get_query = function() {
        if (frm.doc.custom_supplier_agreement) {
            return {
                query: "masar_mce.custom.stock_entry.stock_entry.get_items_from_blanket_order",
                filters: {
                    blanket_order: frm.doc.custom_supplier_agreement
                }
            };
        } else {
            return item_code_field.original_get_query ? item_code_field.original_get_query() : {};
        }
    };
    
    setTimeout(() => {    
            cur_frm.page.remove_inner_button(__('Payment'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Payment Request'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Purchase Order'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Product Bundle'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Material Request'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Supplier Quotation'),  __('Get Items From'));
        },100);
}
frappe.ui.form.on('Purchase Order Item', {
    item_code: function(frm, cdt, cdn) {
        GetItemDetails(frm , cdt , cdn)
    } , 
    rate :  function(frm, cdt, cdn) {
        GetItemDetails(frm , cdt , cdn)
    } , 
});
function GetItemDetails(frm , cdt , cdn){
    const row = locals[cdt][cdn];
        if (!frm.doc.custom_supplier_agreement || !row.item_code) {
            return;
        }
        frappe.call({
            method: "masar_mce.custom.purchase_order.purchase_order.get_rate_and_name_blanket_order_item",
            args: {
                parent: frm.doc.custom_supplier_agreement,
                item_code: row.item_code
            },
            callback: function(r) {
                if (r.message) {
                    const data = r.message;
                    frappe.model.set_value(cdt, cdn, 'against_blanket_order' , 1);
                    frappe.model.set_value(cdt, cdn, 'blanket_order', data.parent);
                    frappe.model.set_value(cdt, cdn,'custom_blanket_order_item', data.name ) ;
                    frappe.model.set_value(cdt, cdn, 'rate', data.rate);
                }
            }
        });
}
function GetAllItemsFromSupplierAgreement(frm) {
    frappe.call({
        method:"masar_mce.custom.purchase_order.purchase_order.get_all_items_from_supplier_agreement", 
        args : {
            supplier_agreement : frm.doc.custom_supplier_agreement
        }, 
        callback:function(r) { 
           if (r.message) {
                frm.clear_table("items");
                r.message.forEach(function (d) {
                    let row = frm.add_child("items");
                    frappe.model.set_value(row.doctype, row.name, "item_code", d.item_code);
                    row.item_code = d.item_code;
                    frappe.model.set_value({
                        doctype: row.doctype,
                        name: row.name,
                        fieldname: "rate",
                        value: d.rate,
                        force_set: true
                    });
                    row.rate = d.rate;
                    row.qty = d.qty;
                });
                frm.refresh_field("items");
            }
        }
    })
}
function GetTermsandPenalitesFromAgreement(frm) {
    if (frm.doc.custom_supplier_agreement) {
    frappe.call({
        method:"masar_mce.custom.purchase_order.purchase_order.get_terms_and_penalities_from_supplier_agreement", 
        args : {
            agreement : frm.doc.custom_supplier_agreement
        }, 
        callback: function(r){
             if (r.message) {
                const data = r.message;
                frm.set_value("tc_name", data.g_terms);
                frm.set_value("terms", data.g_terms_and_cond);
                frm.set_value("custom_tcs_terms", data.s_terms);
                frm.set_value("custom_special_terms", data.s_terms_and_cond);
                frm.set_value("custom_penalties", data.penalties);
             }
             else {
                frm.set_value("tc_name", "");
                frm.set_value("terms", "");
                frm.set_value("custom_tcs_terms", "");
                frm.set_value("custom_special_terms", "");
                frm.set_value("custom_penalties", []);
             }
        }
    });
    } else {
        frm.set_value("tc_name", "");
        frm.set_value("terms", "");
        frm.set_value("custom_tcs_terms", "");
        frm.set_value("custom_special_terms", "");
        frm.set_value("custom_penalties", []);
    }
}
frappe.form.link_formatters['Item'] = function(value, doc) {
    if(doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    } else {
        return value;
    }
};