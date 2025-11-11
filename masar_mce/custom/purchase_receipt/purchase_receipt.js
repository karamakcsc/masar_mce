frappe.ui.form.on("Purchase Receipt", {
    setup(frm) {
        set_item_code_query(frm);
        hide_buttons(frm);
        ChangeLabels(frm);
    }, 
    refresh(frm) {
        set_item_code_query(frm);
        hide_buttons(frm);
        ChangeLabels(frm);
    }, 
    onload(frm) {
        set_item_code_query(frm);
        hide_buttons(frm);
        ChangeLabels(frm);
        if (frm.doc.is_return && frm.doc.docstatus === 0 && frm.is_new()) {
            frm.doc.items.forEach(row => {
                row.custom_request_quantity = row.qty;
                row.qty = -1;
                row.received_qty = -1;
            });
            frm.refresh_field("items");
        }
    }, 
    supplier(frm) {
        set_item_code_query(frm);
    },
    workflow_state(frm) {
        if (frm.doc.docstatus === 0) {
            refresh_item_fields(frm);   
        }
    },
    after_workflow_action(frm) {
        if (frm.doc.docstatus === 0) {
            refresh_item_fields(frm);   
        }
    },
});

function refresh_item_fields(frm) {
    frm.fields_dict["items"].grid.update_docfield_property("rejected_qty", "read_only", ['Purchase Receipt', 'Receipt Return'].indexOf(frm.doc.workflow_state) === -1);
    frm.fields_dict["items"].grid.update_docfield_property("qty", "read_only", ['Purchase Receipt', 'Receipt Return'].indexOf(frm.doc.workflow_state) === -1);
    frm.fields_dict["items"].grid.update_docfield_property("received_qty", "read_only", ['Purchase Receipt', 'Receipt Return'].indexOf(frm.doc.workflow_state) === -1);
    frm.fields_dict["items"].grid.update_docfield_property("custom_request_quantity", "read_only", ['Purchase Receipt', 'Receipt Return'].indexOf(frm.doc.workflow_state) === 1);
    frm.refresh_field("items");
}
function hide_buttons(frm) {
    setTimeout(() => {
        cur_frm.page.remove_inner_button(__('Purchase Invoice'), __('Get Items From'));
        cur_frm.page.remove_inner_button(__('Purchase Order'), __('Get Items From'));
        cur_frm.page.remove_inner_button(__('Make Stock Entry'), __('Create'));
        cur_frm.page.remove_inner_button(__('Landed Cost Voucher'), __('Create'));
        cur_frm.page.remove_inner_button(__('Retention Stock Entry'), __('Create'));
    }, 100);
}

frappe.form.link_formatters['Item'] = function(value, doc) {
    if(doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    } else {
        return value;
    }
};

function set_item_code_query(frm) {
    frm.fields_dict['items'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
        return {
            query: "masar_mce.custom.purchase_receipt.purchase_receipt.get_items_from_open_purchase_orders",
            filters: {
                supplier: frm.doc.supplier
            }
        };
    };
}

frappe.ui.form.on('Purchase Receipt Item', {
    item_code(frm, cdt, cdn) {
        GetItemDetails(frm , cdt , cdn)
    },
    rate(frm, cdt, cdn) {
        GetItemDetails(frm , cdt , cdn)
    }
});
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
            method: "masar_mce.custom.purchase_receipt.purchase_receipt.get_po_details_for_item",
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
                        rate: r.message.rate
                    });
                } else {
                    frappe.model.set_value(cdt, cdn, "purchase_order", null);
                    frappe.model.set_value(cdt, cdn, "purchase_order_item", null);
                    frappe.model.set_value(cdt, cdn, "rate", 0);
                }
            }
        });
    }
function ChangeLabels(frm) {
    const isReturn = frm.doc.is_return === 1;
    frm.set_df_property("custom_delivery_date", "label", isReturn ? "Expected Return Date" : "Expected Delivery Date");
    frm.set_df_property("posting_date", "label", isReturn ? "Return Date" : "Receipt Date");
    frm.refresh_fields();
    frappe.after_ajax(() => {
        $('[data-fieldname="custom_section_break_btshv"] .section-head').text(
            isReturn ? "Return Details" : "Receipt Details"
        );
    });
}
