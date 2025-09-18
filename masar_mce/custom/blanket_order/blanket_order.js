frappe.ui.form.on("Blanket Order", {
    onload: function(frm) {
        filterBySupplier(frm);
    },
    refresh:  function(frm) {
        filterBySupplier(frm);
    },
    setup:  function(frm) {
        filterBySupplier(frm);
    }
});
function filterBySupplier(frm) {
    frm.fields_dict.items.grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
        return {
            query: "masar_mce.custom.blanket_order.blanket_order.get_items_by_supplier",
            filters: {
                supplier: frm.doc.supplier
            }
        };
    };
}