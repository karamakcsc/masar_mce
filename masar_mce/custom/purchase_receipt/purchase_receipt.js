frappe.ui.form.on("Purchase Receipt", {
    setup(frm) {
        FilterItems(frm);
    }, 
    refresh(frm) {
        FilterItems(frm);
    }, 
    onload(frm) {
        FilterItems(frm);
    }, 
    custom_supplier_agreement(frm) {
        GetAllItemsFromSupplierAgreement(frm);
    }
});

function FilterItems(frm) {
    frappe.ui.form.on("Purchase Invoice", "get_items_from_purchase_receipt", function () {
            const d = cur_dialog;
            if (d && d.fields_dict.purchase_receipt) {
                d.fields_dict.purchase_receipt.get_query = function () {
                    return {
                        filters: {
                            supplier_agreement: frm.doc.supplier_agreement
                        }
                    };
                };
            }
        });
    setTimeout(() => {
            cur_frm.page.remove_inner_button(__('Purchase Invoice'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Purchase Order'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Make Stock Entry'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Landed Cost Voucher'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Retention Stock Entry'),  __('Create'));
        },100);
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
frappe.form.link_formatters['Item'] = function(value, doc) {
    if(doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    } else {
        return value;
    }
};
