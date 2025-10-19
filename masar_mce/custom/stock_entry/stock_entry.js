frappe.ui.form.on("Stock Entry", {
    onload: function(frm) {
        FilterForSupplierAgreement(frm);
        FilterWarehouseForInspection(frm);
    }, 
    refresh:function(frm) {
        FilterForSupplierAgreement(frm);
        FilterWarehouseForInspection(frm);
    }, 
    setup: function(frm) {
        FilterWarehouseForInspection(frm);
        FilterForSupplierAgreement(frm);
    },
    stock_entry_type: function(frm) {
        FilterWarehouseForInspection(frm);
        FilterForSupplierAgreement(frm);
    },
});
function FilterForSupplierAgreement(frm) {
    setTimeout(() => {    
            cur_frm.page.remove_inner_button(__('Purchase Invoice'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Bill of Materials'),  __('Get Items From'));
        },100);
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
function FilterWarehouseForInspection(frm) {
    const isInspection =
        frm.doc.stock_entry_type === "Material Receipt for Inspection" ||
        frm.doc.stock_entry_type === "سند إستلام لفحص الجودة";
    const grid = frm.fields_dict["items"].grid;
    const tWarehouseField = grid.get_field("t_warehouse");
    if (!frm._original_to_warehouse_query) {
        frm._original_to_warehouse_query = frm.fields_dict.to_warehouse.get_query;
    }
    if (!tWarehouseField.original_get_query) {
        tWarehouseField.original_get_query = tWarehouseField.get_query;
    }
    if (isInspection) {
        frm.set_query("to_warehouse", function() {
            return { filters: { warehouse_type: 'فحص' } };
        });
        tWarehouseField.get_query = function() {
            return { filters: { warehouse_type: 'فحص' } };
        };
    } 
    else {
        frm.fields_dict.to_warehouse.get_query = frm._original_to_warehouse_query || null;
        tWarehouseField.get_query = tWarehouseField.original_get_query || null;
    }
}
