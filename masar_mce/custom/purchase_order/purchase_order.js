frappe.ui.form.on("Purchase Order", {
    setup(frm) {
        FilterItems(frm);
        CreatePurchaseRequest(frm);
    }, 
    refresh(frm) {
        FilterItems(frm);
        CreatePurchaseRequest(frm);
    }, 
    onload(frm) {
        FilterItems(frm);
        CreatePurchaseRequest(frm);
    }, 
    supplier(frm){
        FilterItems(frm);
    }
});

function FilterItems(frm) {
    masar_mce.buying_cycle.set_item_query(frm, function(...args) {
        if (frm.doc.supplier) {
            return {
                query: "masar_mce.custom.purchase_order.purchase_order.get_items_from_active_blanket_order",
                filters: {
                    supplier: frm.doc.supplier
                }
            };
        } else {
            return masar_mce.buying_cycle.standard_item_query(frm, args);
        }
    });
    if (masar_mce.buying_cycle.is_normal(frm)) return;
    setTimeout(() => {    
            frm.remove_custom_button("Link to Material Request", "Tools");
            frm.remove_custom_button("Update Rate as per Last Purchase", "Tools");
            cur_frm.page.remove_inner_button(__('Payment'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Payment Request'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Purchase Invoice'),  __('Create'));
            cur_frm.page.remove_inner_button(__('Product Bundle'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Material Request'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Supplier Quotation'),  __('Get Items From'));
        },100);
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
        if (masar_mce.buying_cycle.is_normal(frm) || !frm.doc.supplier || !row.item_code) {
            return;
        }
        frappe.call({
            method: "masar_mce.custom.purchase_order.purchase_order.get_blanket_order_for_item",
            args: {
                supplier: frm.doc.supplier,
                item_code: row.item_code
            },
            callback: function(r) {
                if (r.message) {
                    const data = r.message;
                    frappe.model.set_value(cdt, cdn, 'against_blanket_order' , 1);
                    frappe.model.set_value(cdt, cdn, 'blanket_order', data.parent);
                    frappe.model.set_value(cdt, cdn,'custom_blanket_order_item', data.name ) ;
                    frappe.model.set_value(cdt, cdn, 'rate', data.rate);
                }
            }
        });
}
frappe.form.link_formatters['Item'] = masar_mce.buying_cycle.item_link_formatter;
function CreatePurchaseRequest(frm) {
    if (frm.doc.docstatus === 1 && !masar_mce.buying_cycle.is_normal(frm)) {
            frm.add_custom_button(__('Market Purchase Request'), function() {
                frappe.model.open_mapped_doc({
                    method: "masar_mce.custom.purchase_order.purchase_order.create_purchase_request_from_purchase_order",
                    frm: cur_frm,
                    freeze_message: __("Creating Market Purchase Request ..."),
                });
            }, __('Create'));
        }
}