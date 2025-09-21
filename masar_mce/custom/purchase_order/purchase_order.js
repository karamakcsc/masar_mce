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
                    if (row.rate === 0 ){
                        frappe.model.set_value(cdt, cdn, 'rate', data.rate);
                    }
                }
            }
        });
}