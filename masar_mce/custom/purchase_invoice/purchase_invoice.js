frappe.ui.form.on("Purchase Invoice", {
    setup(frm) {
        FilterItems(frm);
    }, 
    refresh(frm) {
        FilterItems(frm);
    }, 
    onload(frm) {
        FilterItems(frm);
    }, 
    custom_supplier_agreement(frm){
        GetTermsandPenalitesFromAgreement(frm);
    }
});

function FilterItems(frm) {
    setTimeout(() => {    
            cur_frm.page.remove_inner_button(__('Purchase Order'),  __('Get Items From'));
        },100);
        cur_frm.page.remove_inner_button(__('Purchase Receipt'),  __('Get Items From'));
       frm.add_custom_button(__('Purchase Receipt'), function () {
            if (!frm.doc.custom_supplier_agreement) {
                frappe.msgprint({
                    title: __('Warning'),
                    indicator: 'orange',
                    message: __('Please select a Supplier Agreement first before creating a Purchase Invoice.')
                });
                return; 
            }
            const get_query_filters = {
                docstatus: 1,
                status: ["not in", ["Closed", "Completed", "Return Issued"]],
                company: frm.doc.company,
                supplier: frm.doc.supplier,
                is_return: 0
            };
            if (frm.doc.custom_supplier_agreement) {
                get_query_filters.custom_supplier_agreement = frm.doc.custom_supplier_agreement;
            }
            const mapper = erpnext.utils.map_current_doc({
                method: "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice",
                source_doctype: "Purchase Receipt",
                target: frm,
                setters: {
                    supplier: frm.doc.supplier || undefined,
                    posting_date: undefined,
                },
                get_query_filters: get_query_filters,
                allow_child_item_selection: true,
                child_fieldname: "items",
                child_columns: ["item_code", "item_name", "qty", "amount", "billed_amt"],
            });
            frappe.after_ajax(() => {
                if (cur_dialog && cur_dialog.fields_dict.custom_supplier_agreement) {
                    const field = cur_dialog.fields_dict.custom_supplier_agreement;
                    field.df.read_only = 1;
                    field.refresh();
                }
            });
        }, __('Get Items From'));
    
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
             }
             else {
                frm.set_value("tc_name", "");
                frm.set_value("terms", "");
                frm.set_value("custom_tcs_terms", "");
                frm.set_value("custom_special_terms", "");
             }
        }
    });
    } else {
        frm.set_value("tc_name", "");
        frm.set_value("terms", "");
        frm.set_value("custom_tcs_terms", "");
        frm.set_value("custom_special_terms", "");
    }
}
frappe.form.link_formatters['Item'] = function(value, doc) {
    if(doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    } else {
        return value;
    }
};