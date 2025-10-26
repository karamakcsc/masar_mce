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
    }, 
    supplier(frm) {
        set_item_code_query(frm);
    },
    workflow_state(frm) {
        if (frm.doc.docstatus === 0) {
            frm.refresh_fields();
            frm.fields_dict["items"].grid.refresh();
            frm.trigger("refresh");
        }
    },
    after_workflow_action(frm) {
        if (frm.doc.docstatus === 0) {
            frm.refresh_fields();
            frm.fields_dict["items"].grid.refresh();
            frm.trigger("refresh");
        }
    },
});

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
});
function ChangeLabels(frm) {
    const isReturn = frm.doc.is_return === 1;
    frm.set_df_property("custom_request_date", "label", isReturn ? "Return Date" : "Request Date");
    if (frm.fields_dict["items"]) {
            frm.fields_dict["items"].grid.update_docfield_property(
                "custom_request_quantity", "label",
                isReturn ? "Return Quantity" : "Request Quantity"
            );
        }
        
    frm.refresh_fields();
    frappe.after_ajax(() => {
        $('[data-fieldname="custom_section_break_dvar1"] .section-head').text(
            isReturn ? "Return Details" : "Request Details"
        );
    });
}
