frappe.ui.form.on("Stock Entry", {
    onload: function(frm) {
        FilterForSupplierAgreement(frm);
    }, 
    refresh:function(frm) {
        FilterForSupplierAgreement(frm);
    }, 
    setup: function(frm) {
        FilterForSupplierAgreement(frm);
    }
});
function FilterForSupplierAgreement(frm) {
    const grid = frm.fields_dict.items.grid;
    const item_code_field = grid.get_field("item_code");
    if (!item_code_field.hasOwnProperty("original_get_query")) {
        item_code_field.original_get_query = item_code_field.get_query;
    }
    item_code_field.get_query = function (doc, cdt, cdn) {
        if (
            doc.stock_entry_type &&
            (doc.stock_entry_type === "Material Receipt for Inspection" ||
             doc.stock_entry_type === "سند إستلام لفحص الجودة") &&
            doc.custom_supplier_agreement
        ) {
            return {
                query: "masar_mce.custom.stock_entry.stock_entry.get_items_from_blanket_order",
                filters: {
                    blanket_order: doc.custom_supplier_agreement
                }
            };
        }
        if (typeof item_code_field.original_get_query === "function") {
            return item_code_field.original_get_query(doc, cdt, cdn);
        }
        return {};
    };
}
frappe.form.link_formatters['Item'] = function(value, doc) {
    if(doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    } else {
        return value;
    }
};

