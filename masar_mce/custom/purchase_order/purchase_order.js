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
    supplier(frm){
        FilterItems(frm);
    }
});

function FilterItems(frm) {
    const grid = frm.fields_dict.items.grid;
    const item_code_field = grid.get_field("item_code");
    if (!item_code_field.hasOwnProperty('original_get_query')) {
        item_code_field.original_get_query = item_code_field.get_query;
    }
    
    item_code_field.get_query = function() {
        if (frm.doc.supplier) {
            return {
                query: "masar_mce.custom.purchase_order.purchase_order.get_items_from_active_blanket_order",
                filters: {
                    supplier: frm.doc.supplier
                }
            };
        } else {
            return item_code_field.original_get_query ? item_code_field.original_get_query() : {};
        }
    };
    
    setTimeout(() => {    
            cur_frm.page.remove_inner_button(__('Payment'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Payment Request'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Purchase Invoice'),  __('Create'));
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
        if (!frm.doc.supplier || !row.item_code) {
            return;
        }
        frappe.call({
            method: "masar_mce.custom.purchase_order.purchase_order.get_blanket_order_for_item",
            args: {
                supplier: frm.doc.supplier,
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
frappe.form.link_formatters['Item'] = function(value, doc) {
    if(doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    } else {
        return value;
    }
};