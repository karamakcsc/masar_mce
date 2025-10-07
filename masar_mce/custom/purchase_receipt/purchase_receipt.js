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
