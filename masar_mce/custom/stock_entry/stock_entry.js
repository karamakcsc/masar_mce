frappe.ui.form.on("Stock Entry", {
    onload: function(frm) {
        FilterForSupplierAgreement(frm);
        FilterWarehouseForInspection(frm);
        FilterWarehouseForBonus(frm);
        SetTransitTargetWarehouse(frm);
    }, 
    refresh:function(frm) {
        FilterForSupplierAgreement(frm);
        FilterWarehouseForInspection(frm);
        FilterWarehouseForBonus(frm);
        SetTransitTargetWarehouse(frm);
    }, 
    setup: function(frm) {
        FilterWarehouseForInspection(frm);
        FilterForSupplierAgreement(frm);
        FilterWarehouseForBonus(frm);
    },
    stock_entry_type: function(frm) {
        FilterWarehouseForInspection(frm);
        FilterWarehouseForBonus(frm);
        FilterForSupplierAgreement(frm);
    },
    add_to_transit: function(frm) {
        SetTransitWarehouse(frm);
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
        if (
            doc.stock_entry_type &&
            (doc.stock_entry_type === "Return to Supplier" || doc.stock_entry_type ===  "إرجاع إلى المورد") &&
            doc.custom_supplier
        ) {
            return {
                query: "masar_mce.custom.stock_entry.stock_entry.get_items_from_party_specific_item",
                filters: {
                    party: doc.custom_supplier,
                    party_type: "Supplier"
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
function FilterWarehouseForBonus(frm) {
    frm.set_query("custom_target_location", function () {
        return {
            filters: {
                warehouse_type: ["in", ["سوق", "مستودع"]]
            }
        };
    });
    const isBonus =
        frm.doc.stock_entry_type === "Bonus Receipt" ||
        frm.doc.stock_entry_type === 'سند استلام البونص';

    const grid = frm.fields_dict["items"].grid;
    const tWarehouseField = grid.get_field("t_warehouse");

    if (!frm._original_bonus_to_warehouse_query) {
        frm._original_bonus_to_warehouse_query =
            frm.fields_dict.to_warehouse.get_query;
    }

    if (!tWarehouseField.original_bonus_get_query) {
        tWarehouseField.original_bonus_get_query =
            tWarehouseField.get_query;
    }

    if (isBonus) {
        frm.set_query("to_warehouse", function () {
            return {
                filters: {
                    warehouse_type: ["in", ["Bouns", "بونص"]]
                }
            };
        });

        tWarehouseField.get_query = function () {
            return {
                filters: {
                    warehouse_type: ["in", ["Bouns", "بونص"]]
                }
            };
        };
    }
}

function SetTransitWarehouse(frm) {
    if (frm.doc.purpose === 'Material Transfer' && frm.doc.add_to_transit) {
        frappe.call({
            method: 'masar_mce.custom.stock_entry.stock_entry.get_transit_warehouse',
            args: { company: frm.doc.company },
            callback: (r) => {
                if (r.message) {
                    frm.set_value('to_warehouse', r.message);
                } else {
                    frappe.msgprint(__('No transit warehouse configured for {0}', [frm.doc.company]));
                }
            }
        });
    }
}

function SetTransitTargetWarehouse(frm) {
    if (
        frm.doc.outgoing_stock_entry &&
        frm.doc.custom_target_location &&
        frm.doc.docstatus === 0
    ) {
        frm.set_value('to_warehouse', frm.doc.custom_target_location);

        (frm.doc.items || []).forEach(row => {
            frappe.model.set_value(row.doctype, row.name, 't_warehouse', frm.doc.custom_target_location);
        });
        frm.refresh_field('items');
    }
}