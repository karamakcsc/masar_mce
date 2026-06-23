// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Inspection Details', {
    supply_date: function(frm, cdt, cdn) { calculate_child_row(frm, cdt, cdn); },
    production_date: function(frm, cdt, cdn) { calculate_child_row(frm, cdt, cdn); },
    expiry_date: function(frm, cdt, cdn) { calculate_child_row(frm, cdt, cdn); },
    item_code: function(frm, cdt, cdn) { 
        get_selling_price_from_supplier_agreement(frm, cdt, cdn);
        validate_item_against_purchase_receipt(frm, cdt, cdn);
        let current_item_code = locals[cdt][cdn].item_code;
        if (!current_item_code) return;
        
        let items_table = frm.doc.items || [];
        let count = 0;
        for (let row of items_table) {
            if (row.item_code === current_item_code) count++;
        }
        if (count > 1) {
                frappe.msgprint(__("Item {0} has already been added. Duplicate entries are not allowed.").format(current_item_code));
                frappe.model.set_value(cdt, cdn, 'item_code', '');
                frm.refresh_field('items');
        }
    }
});

frappe.ui.form.on('Material Inspection', {
    purchase_receipt: function(frm) {
        set_item_code_filter(frm);
        frm.clear_table('items');
        frm.refresh_field('items');
        if (frm.doc.purchase_receipt) {
            frappe.call({
                method: "frappe.client.get",
                args: { doctype: "Purchase Receipt", name: frm.doc.purchase_receipt },
                callback: function(r) {
                    if (r.message && r.message.docstatus !== 0) {
                        frappe.msgprint(__("Selected Purchase Receipt is not in Draft status. Please select a Draft receipt."));
                        frappe.model.set_value(frm.doctype, frm.docname, 'purchase_receipt', '');
                        set_item_code_filter(frm);
                    }
                }
            });
        } else {
            set_item_code_filter(frm); 
        }
    }, 
    setup: function(frm){
        frm.set_df_property('items', 'cannot_add_rows', true);
        frm.set_df_property('items', 'cannot_delete_rows', true); 
        frm.set_df_property('items', 'cannot_delete_all_rows', true);
    }
});
function set_item_code_filter(frm) {
    const grid = frm.fields_dict.items.grid;
    const item_code_field = grid.get_field("item_code");
    if (!item_code_field._original_get_query) {
        item_code_field._original_get_query = item_code_field.get_query;
    }
    if (frm.doc.purchase_receipt) {
        item_code_field.get_query = function() {
            return {
                query: "masar_mce.masar_mce.doctype.material_inspection.material_inspection.get_items_from_purchase_receipt",
                filters: {
                    purchase_receipt: frm.doc.purchase_receipt
                }
            };
        };
    } else {
        item_code_field.get_query = item_code_field._original_get_query || function() { return {}; };
    }
    grid.refresh();
}

function calculate_child_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let changed = false;
    if (row.supply_date && row.production_date) {
        let days = frappe.datetime.get_diff(row.supply_date, row.production_date);
        if (row.delay_period !== days) {
            row.delay_period = days;
            changed = true;
        }
    } else if (row.delay_period) {
        row.delay_period = null;
        changed = true;
    }
    if (row.production_date && row.expiry_date) {
        if (frappe.datetime.get_diff(row.expiry_date, row.production_date) < 0) {
            frappe.throw(__("Expiry date cannot be before Production date"));
        }
        let prod_date = frappe.datetime.str_to_obj(row.production_date);
        let exp_date = frappe.datetime.str_to_obj(row.expiry_date);
        let months_diff = (exp_date.getFullYear() - prod_date.getFullYear()) * 12;
        months_diff += exp_date.getMonth() - prod_date.getMonth();
        if (exp_date.getDate() < prod_date.getDate()) {
            months_diff -= 1;
        }
        let years = Math.floor(months_diff / 12);
        let months = months_diff % 12;
        let parts = [];
        if (years > 0) {
            parts.push(years + " year" + (years !== 1 ? "s" : ""));
        }
        if (months > 0) {
            parts.push(months + " month" + (months !== 1 ? "s" : ""));
        }
        let lifespan_str = parts.join(" ") || "0 months";
        if (row.product_lifespan !== lifespan_str) {
            row.product_lifespan = lifespan_str;
            changed = true;
        }
    } else if (row.product_lifespan) {
        row.product_lifespan = null;
        changed = true;
    }
    if (row.supply_date && row.production_date && row.expiry_date) {
        let total_lifespan = frappe.datetime.get_diff(row.expiry_date, row.production_date);
        if (total_lifespan > 0) {
            let used_days = frappe.datetime.get_diff(row.supply_date, row.production_date);
            let percent = (used_days / total_lifespan) * 100;
            percent = Math.round(percent * 100) / 100;
            if (row.production_exceeded !== percent) {
                row.production_exceeded = percent;
                changed = true;
            }
        } else if (row.production_exceeded) {
            row.production_exceeded = null;
            changed = true;
        }
    } else if (row.production_exceeded) {
        row.production_exceeded = null;
        changed = true;
    }
    
    if (changed) {
        frappe.model.set_value(cdt, cdn, 'delay_period', row.delay_period);
        frappe.model.set_value(cdt, cdn, 'product_lifespan', row.product_lifespan);
        frappe.model.set_value(cdt, cdn, 'production_exceeded', row.production_exceeded);
        frm.refresh_field('items');
    }
}

function get_selling_price_from_supplier_agreement(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!frm.doc.supplier || !row.item_code) {
        return;
    }
    frappe.call({
        doc: frm.doc,
        method: "get_selling_price_from_supplier_agreement",
        args: {
            supplier: frm.doc.supplier,
            item_code: row.item_code
        },
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                frappe.model.set_value(cdt, cdn, 'selling_price', data.selling_price);
            }
        }
    });
}
function validate_item_against_purchase_receipt(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!frm.doc.purchase_receipt || !row.item_code) return;
    frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Purchase Receipt", name: frm.doc.purchase_receipt },
        callback: function(r) {
            if (r.message) {
                let pr = r.message;
                let item_codes = (pr.items || []).map(i => i.item_code);
                if (!item_codes.includes(row.item_code)) {
                    frappe.msgprint(__("Item {0} is not present in the selected Purchase Receipt {1}. It will be removed.").format(row.item_code, frm.doc.purchase_receipt));
                    frappe.model.set_value(cdt, cdn, 'item_code', '');
                    frm.refresh_field('items');
                }
            }
        }
    });
}