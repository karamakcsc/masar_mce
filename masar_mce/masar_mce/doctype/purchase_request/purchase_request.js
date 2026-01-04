// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Request", {
	refresh(frm) {
        set_item_code_query(frm);
        GetItemsFromPO(frm);
	},
    setup(frm) {
        set_item_code_query(frm);
    },
    onload(frm) {
        set_item_code_query(frm);
    },
    supplier(frm) {
        set_item_code_query(frm);
    }
});
function set_item_code_query(frm) {
    frm.fields_dict['items'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
        return {
            query: "masar_mce.masar_mce.doctype.purchase_request.purchase_request.get_items_from_open_purchase_orders",
            filters: {
                supplier: frm.doc.supplier
            }
        };
    };
}

frappe.ui.form.on('Purchase Request Item', {
    item_code(frm, cdt, cdn) {
        GetItemDetails(frm , cdt , cdn)
    }, 
    rate(frm, cdt, cdn) {
        GetAmount(frm , cdt , cdn);
        GetTotals(frm);
    }, 
    request_quantity(frm, cdt, cdn) {
        GetAmount(frm , cdt , cdn);
        GetTotals(frm);
    }, 
    items_remove(frm, cdt, cdn) {
        GetTotals(frm);
    }
});
function GetAmount(frm , cdt , cdn){
    const row = locals[cdt][cdn];
        if (!row.rate || !row.request_quantity) return;
        
        let amount = row.rate * row.request_quantity;
        frappe.model.set_value(cdt, cdn, "amount", amount);
    }
function GetTotals(frm){
    let total_amount = 0;
    let total_quantity = 0;
    frm.doc.items.forEach(r => {
        total_amount += r.amount ? r.amount : 0;
        total_quantity += r.request_quantity ? r.request_quantity : 0;
    });
    frm.set_value("total", total_amount);
    frm.set_value("total_quantity", total_quantity);
}
function GetItemDetails(frm , cdt , cdn){
    const row = locals[cdt][cdn];
        if (!row.item_code || !frm.doc.supplier) return;
        
        let used_pos = [];
        frm.doc.items.forEach(r => {
            if (r.item_code === row.item_code && r.purchase_order && r.idx !== row.idx) {
                used_pos.push(r.purchase_order);
            }
        });
        
        frappe.call({
            method: "masar_mce.masar_mce.doctype.purchase_request.purchase_request.get_po_details_for_item",
            args: {
                item_code: row.item_code,
                supplier: frm.doc.supplier,
                used_pos: used_pos
            },
            callback: function(r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, {
                        purchase_order: r.message.purchase_order,
                        purchase_order_item: r.message.purchase_order_item, 
                        rate:r.message.rate
                    });
                } else {
                    frappe.model.set_value(cdt, cdn, "purchase_order", null);
                    frappe.model.set_value(cdt, cdn, "purchase_order_item", null);
                }
            }
        });
    }
function GetItemsFromPO(frm) {
    if (frm.doc.docstatus === 0) {
        frm.add_custom_button(
            __("Purchase Order"),
            function () {

                if (!frm.doc.supplier) {
                    frappe.throw({
                        title: __("Mandatory"),
                        message: __("Please Select a Supplier"),
                    });
                }

                erpnext.utils.map_current_doc({
                    method: "masar_mce.masar_mce.doctype.purchase_request.purchase_request.make_purchase_request",
                    source_doctype: "Purchase Order",
                    target: frm,
                    setters: {
                        supplier: frm.doc.supplier,
                    },
                    get_query_filters: {
                        docstatus: 1,
                        status: ["not in", ["Closed", "On Hold"]],
                        company: frm.doc.company,
                    },
                    allow_child_item_selection: true,
                    child_fieldname: "items",
                    child_columns: [
                        "item_code",
                        "item_name",
                        "qty",
                        "rate"
                    ],
                });
            },
            __("Get Items From")
        );
    }
    if (frm.doc.docstatus === 1) {
    frm.add_custom_button(
        __("Purchase Receipt"),
        function () {
            frappe.model.open_mapped_doc({
            method: "masar_mce.masar_mce.doctype.purchase_request.purchase_request.make_purchase_receipt_from_purchase_request",
            frm: frm,
            freeze_message: __("Creating Purchase Receipt ..."),
        });

        },
        __("Create")
    );
}
}
