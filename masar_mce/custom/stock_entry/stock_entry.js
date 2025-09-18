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
    frm.fields_dict.items.grid.get_field("item_code").get_query = function(doc, cdt, cdn) {
        if (doc.stock_entry_type === "Material Receipt for Inspection" && doc.custom_supplier_agreement) {
            return {
                query: "masar_mce.custom.stock_entry.stock_entry.get_items_from_blanket_order",
                filters: {
                    blanket_order: doc.custom_supplier_agreement
                }
            };
        }
        return {};
    };
}
