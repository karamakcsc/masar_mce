// Client Script for Pricing Sheet (updated Nov 2025)
// Dynamic calculations on client matching server validate logic
frappe.ui.form.on("Pricing Sheet", {
    refresh(frm) {
        set_item_query(frm);
        GetItemsDialog(frm);
        GetLastSync(frm);
    },
    blanket_order(frm) {
        set_item_query(frm);
        GetItemsDialog(frm);
    },
    setup(frm) {
        set_item_query(frm);
        GetItemsDialog(frm);
        GetLastSync(frm);
    }
});
frappe.ui.form.on("Pricing Sheet Items", {
    item_code(frm, cdt, cdn) {
        fetch_tax_and_stock_then_recalc(frm, cdt, cdn);
    },
    new_purchase_price(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    new_quantity(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    current_stock_value(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    current_quantity(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    local_sp(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    free_sp(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    items_remove(frm) {
        GetTotals(frm);
    },
    local_mp(frm, cdt, cdn) {
        calculate_local_sp(frm, cdt, cdn);
    },
    free_mp(frm, cdt, cdn) {
        calculate_free_sp(frm, cdt, cdn);
    }
});
function fetch_tax_and_stock_then_recalc(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row.item_code) {
        row.local_tax_rate = 0;
        row.free_tax_rate = 0;
        row.current_stock_value = 0;
        row.current_quantity = 0;
        frm.refresh_field("items");
        recalc_row_and_totals(frm, cdt, cdn);
        return;
    }
    let tax_promise = frappe.xcall
        ? frappe.xcall('masar_mce.utils.get_tax_for_item', { item_code: row.item_code, category: 'Local Zone' })
        : frappe.call({ method: 'masar_mce.utils.get_tax_for_item', args: { item_code: row.item_code, category: 'Local Zone' } });

    let tax_promise_free = frappe.xcall
        ? frappe.xcall('masar_mce.utils.get_tax_for_item', { item_code: row.item_code, category: 'Free Zone' })
        : frappe.call({ method: 'masar_mce.utils.get_tax_for_item', args: { item_code: row.item_code, category: 'Free Zone' } });

    let stock_promise = frappe.xcall
        ? frappe.xcall('masar_mce.utils.get_current_stock_value_and_quantity', { item_code: row.item_code })
        : frappe.call({ method: 'masar_mce.utils.get_current_stock_value_and_quantity', args: { item_code: row.item_code } });
    Promise.all([tax_promise, tax_promise_free, stock_promise]).then(results => {
        const local_tax_result = results[0].message !== undefined ? results[0].message : results[0];
        const free_tax_result = results[1].message !== undefined ? results[1].message : results[1];
        const stock_result = results[2].message !== undefined ? results[2].message : results[2];
        row.local_tax_rate = flt(local_tax_result) * 100;
        row.free_tax_rate = flt(free_tax_result) * 100;
        row.current_stock_value = flt(stock_result.value || stock_result.message && stock_result.message.value || 0);
        row.current_quantity = flt(stock_result.quantity || stock_result.message && stock_result.message.quantity || 0);
        recalc_row_and_totals(frm, cdt, cdn);
    }).catch(err => {
        frappe.call({
            method: 'masar_mce.utils.get_tax_for_item',
            args: { item_code: row.item_code, category: 'Local Zone' },
            callback: function(r) {
                row.local_tax_rate = flt(r.message) * 100;
                frappe.call({
                    method: 'masar_mce.utils.get_tax_for_item',
                    args: { item_code: row.item_code, category: 'Free Zone' },
                    callback: function(r2) {
                        row.free_tax_rate = flt(r2.message) * 100;
                        frappe.call({
                            method: 'masar_mce.utils.get_current_stock_value_and_quantity',
                            args: { item_code: row.item_code },
                            callback: function(r3) {
                                row.current_stock_value = flt(r3.message.value || 0);
                                row.current_quantity = flt(r3.message.quantity || 0);
                                frm.refresh_field("items");
                                recalc_row_and_totals(frm, cdt, cdn);
                            }
                        });
                    }
                });
            }
        });
    });
}
function calculate_local_sp(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let local_sp = flt(row.local_pp_after_tax) * (1 + flt(row.local_mp) / 100);
    row.local_sp = local_sp;
    row.local_sp_after_tax = flt(local_sp) * (1 + flt(row.local_tax_rate) / 100);
    frm.refresh_field("items");
}
function calculate_free_sp(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let free_sp = flt(row.free_pp_after_tax) * (1 + flt(row.free_mp) / 100);
    row.free_sp = free_sp;
    row.free_sp_after_tax = flt(free_sp) * (1 + flt(row.free_tax_rate) / 100);
    frm.refresh_field("items");
}
function recalc_row_and_totals(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.current_stock_value = flt(row.current_stock_value);
    row.current_quantity = flt(row.current_quantity);
    row.new_purchase_price = flt(row.new_purchase_price);
    row.new_quantity = flt(row.new_quantity);
    let local_tax_decimal = flt(row.local_tax_rate) / 100.0;
    let free_tax_decimal = flt(row.free_tax_rate) / 100.0;
    row.local_pp_after_tax = flt(row.new_purchase_price) * (1 + local_tax_decimal);
    row.free_pp_after_tax = flt(row.new_purchase_price) * (1 + free_tax_decimal);
    row.local_sp = flt(row.local_pp_after_tax) * (1 + flt(row.local_mp) / 100);
    row.free_sp = flt(row.free_pp_after_tax) * (1 + flt(row.free_mp) / 100);
    let denom = flt(row.current_quantity) + flt(row.new_quantity);
    row.new_cost_per_unit = denom > 0 ? (flt(row.current_stock_value) + flt(row.new_purchase_price) * flt(row.new_quantity)) / denom : 0;
    row.local_mp = flt(row.new_purchase_price) > 0 ? (flt(row.local_sp) - flt(row.local_pp_after_tax)) / flt(row.local_pp_after_tax) * 100 : 0;
    row.free_mp = flt(row.new_purchase_price) > 0 ? (flt(row.free_sp) - flt(row.free_pp_after_tax)) / flt(row.free_pp_after_tax) * 100 : 0;
    row.local_sp_after_tax = flt(row.local_sp) * (1 + local_tax_decimal);
    row.free_sp_after_tax = flt(row.free_sp) * (1 + free_tax_decimal);
    frm.refresh_field("items");
    GetTotals(frm);
}
function GetTotals(frm) {
    let new_total_quantity = 0;
    let local_sa = 0;
    let free_sa = 0;
    let new_purchase_amount = 0;

    (frm.doc.items || []).forEach(row => {
        new_total_quantity += flt(row.new_quantity);
        local_sa += flt(row.new_quantity) * flt(row.local_sp_after_tax);
        free_sa += flt(row.new_quantity) * flt(row.free_sp_after_tax);
        new_purchase_amount += flt(row.new_quantity) * flt(row.new_purchase_price);
    });

    frm.set_value("new_total_quantity", new_total_quantity);
    frm.set_value("local_sa", local_sa);
    frm.set_value("free_sa", free_sa);
    frm.set_value("new_purchase_amount", new_purchase_amount);

    frm.refresh_fields();
}
function GetItemsDialog(frm) {
    if (!frm.doc.blanket_order) {
        return;
    }
    frm.add_custom_button("Get Items", () => {
        frappe.call({
            method: "masar_mce.masar_mce.doctype.pricing_sheet.pricing_sheet.get_items_for_dialog",
            args: { blanket_order: frm.doc.blanket_order },
            callback: async function(r) {
                if (!r.message || !r.message.length) {
                    frappe.msgprint("No items found in this Supplier Agreement.");
                    return;
                }
                let existing_items = (frm.doc.items || []).map(i => i.item_code);
                let remaining_items = r.message.filter(i => !existing_items.includes(i.item_code));
                let data = [];
                for (let item of remaining_items) {
                    let stock_info = await frappe.call({
                        method: "masar_mce.utils.get_current_stock_value_and_quantity",
                        args: { item_code: item.item_code }
                    });
                    let tax_local = await frappe.call({
                        method: "masar_mce.utils.get_tax_for_item",
                        args: { item_code: item.item_code, category: 'Local Zone' }
                    });
                    let tax_free = await frappe.call({
                        method: "masar_mce.utils.get_tax_for_item",
                        args: { item_code: item.item_code, category: 'Free Zone' }
                    });

                    let local_tax_rate = flt(tax_local.message) * 100;
                    let free_tax_rate = flt(tax_free.message) * 100;

                    let new_purchase_price = flt(item.custom_purchase_price || item.rate || 0);
                    let new_quantity = flt(item.custom_qty || 0);

                    let local_pp_after_tax = flt(new_purchase_price) * (1 + flt(tax_local.message));
                    let free_pp_after_tax = flt(new_purchase_price) * (1 + flt(tax_free.message));
                    let local_sp = flt(local_pp_after_tax) * (1 + flt(item.custom_markup_percentage || 0) / 100);
                    let free_sp = flt(free_pp_after_tax) * (1 + flt(item.custom_markup_percentage || 0) / 100);
                    data.push({
                        item_code: item.item_code,
                        item_name: item.item_name,
                        current_stock_value : flt(stock_info.message.value || 0),
                        current_quantity :  flt(stock_info.message.quantity || 0),
                        new_purchase_price: new_purchase_price,
                        new_quantity: new_quantity,
                        new_cost_per_unit: flt(flt(stock_info.message.value || 0) + new_purchase_price * new_quantity) / flt(flt(stock_info.message.quantity || 0) + new_quantity),
                        local_tax_rate : local_tax_rate,
                        free_tax_rate : free_tax_rate,
                        local_pp_after_tax: local_pp_after_tax,
                        free_pp_after_tax: free_pp_after_tax,
                        local_mp : flt(item.custom_markup_percentage || 0) , 
                        free_mp : flt(item.custom_markup_percentage || 0) ,
                        local_sp: local_sp,
                        free_sp: free_sp,
                        local_sp_after_tax: flt(local_sp) * (1 + flt(tax_local.message)),
                        free_sp_after_tax: flt(free_sp) * (1 + flt(tax_free.message))
                    });
                }

                const dialog = new frappe.ui.Dialog({
                    title: __("Select Items to Add"),
                    size: "extra-large",
                    fields: [
                        {
                            fieldname: "items_table",
                            fieldtype: "Table",
                            label: __("Items"),
                            in_place_edit: true,
                            cannot_add_rows: true,
                            cannot_delete_rows: true,
                            get_data: () => data,
                            fields: [
                                { fieldname: "item_code", label: "Item Code", fieldtype: "Data", read_only: 1, width: 120, in_list_view: 1 },
                                { fieldname: "item_name", label: "Item Name", fieldtype: "Data", read_only: 1, width: 200, in_list_view: 1 },
                                { fieldname: "new_purchase_price", label: "New Purchase Price", fieldtype: "Currency", width: 120, in_list_view: 1 },
                                { fieldname: "new_quantity", label: "New Qty", fieldtype: "Float", width: 100, in_list_view: 1 },
                                { fieldname: "current_stock_value", label: "Current Stock Value", fieldtype: "Currency", read_only: 1, width: 140, in_list_view: 1 },
                                { fieldname: "current_quantity", label: "Current Qty", fieldtype: "Float", read_only: 1, width: 100, in_list_view: 1 },
                                { fieldname: "local_tax_rate", label: "Local Tax %", fieldtype: "Percent", read_only: 1, width: 100, in_list_view: 1 },
                                { fieldname: "free_tax_rate", label: "Free Tax %", fieldtype: "Percent", read_only: 1, width: 100, in_list_view: 1 },
                                { fieldname: "local_pp_after_tax", label: "Purch. After Tax (Local)", fieldtype: "Currency", read_only: 1, width: 140, in_list_view: 1 },
                                { fieldname: "free_pp_after_tax", label: "Purch. After Tax (Free)", fieldtype: "Currency", read_only: 1, width: 140, in_list_view: 1 },
                                { fieldname: "local_sp", label: "Local SP", fieldtype: "Currency", width: 120, in_list_view: 1 },
                                { fieldname: "local_sp_after_tax", label: "Local SP After Tax", fieldtype: "Currency", read_only: 1, width: 160, in_list_view: 1 },
                                { fieldname: "free_sp", label: "Free SP", fieldtype: "Currency", width: 120, in_list_view: 1 },
                                { fieldname: "free_sp_after_tax", label: "Free SP After Tax", fieldtype: "Currency", read_only: 1, width: 160, in_list_view: 1 }
                            ]
                        }
                    ],
                    primary_action_label: __("Add Selected Items"),
                    primary_action: () => {
                        const selected_rows = dialog.fields_dict.items_table.grid.get_selected_children();
                        selected_rows.forEach(row => {
                            if (!frm.doc.items.some(i => i.item_code === row.item_code)) {
                                let new_row = frm.add_child("items");
                                new_row.item_code = row.item_code;
                                new_row.item_name = row.item_name;
                                new_row.current_stock_value = flt(row.current_stock_value || 0);
                                new_row.current_quantity =  flt(row.current_quantity || 0);
                                new_row.new_purchase_price = row.new_purchase_price;
                                new_row.new_quantity = row.new_quantity;
                                new_row.new_cost_per_unit = row.new_cost_per_unit;
                                new_row.local_tax_rate = row.local_tax_rate;
                                new_row.free_tax_rate = row.free_tax_rate;
                                new_row.local_pp_after_tax = row.local_pp_after_tax;
                                new_row.free_pp_after_tax = row.free_pp_after_tax;
                                new_row.local_mp = flt(row.local_mp || 0) ; 
                                new_row.free_mp = flt(row.free_mp || 0) ;
                                new_row.local_sp = row.local_sp;
                                new_row.free_sp = row.free_sp;
                                new_row.local_sp_after_tax = flt(row.local_sp_after_tax) ;
                                new_row.free_sp_after_tax = flt(row.free_sp_after_tax);
                            }
                        });
                        frm.refresh_field("items");
                        (frm.doc.items || []).forEach((r, idx) => {
                            recalc_row_and_totals(frm, r.doctype ? r.doctype : frm.doctype, r.name);
                        });
                        dialog.hide();
                    }
                });
                dialog.show();
            }
        });
    });
}
function GetLastSync(frm) {
    frappe.call({
        doc: frm.doc,
        method: "get_last_sync",
        callback: function(r) {
            if (r.message) {
                frm.doc.last_sync = r.message;
                frm.refresh_field("last_sync");
            }
        }
    });
}
function set_item_query(frm) {
    frm.fields_dict["items"].grid.get_field("item_code").get_query = function(doc, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!frm.doc.blanket_order) {
            frappe.msgprint({
                title: __("Supplier Agreement Required"),
                indicator: "red",
                message: __("Please select a Supplier Agreement before adding items.")
            });
            return { filters: { item_code: " " } };
        }
        return {
            query: "masar_mce.masar_mce.doctype.pricing_sheet.pricing_sheet.get_items_by_blanket_order",
            filters: {
                blanket_order: frm.doc.blanket_order
            }
        };
    };
}
