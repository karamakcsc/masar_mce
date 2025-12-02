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
    local_curr_stock_value(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    local_curr_qty(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    free_curr_stock_value(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    free_curr_qty(frm, cdt, cdn) {
        recalc_row_and_totals(frm, cdt, cdn);
    },
    local_sp(frm, cdt, cdn) {
        update_markup_from_selling_price(frm, cdt, cdn, 'local');
    },
    free_sp(frm, cdt, cdn) {
        update_markup_from_selling_price(frm, cdt, cdn, 'free');
    },
    items_remove(frm) {
        GetTotals(frm);
    },
    local_mp(frm, cdt, cdn) {
        update_selling_price_from_markup(frm, cdt, cdn, 'local');
    },
    free_mp(frm, cdt, cdn) {
        update_selling_price_from_markup(frm, cdt, cdn, 'free');
    }
});
function update_markup_from_selling_price(frm, cdt, cdn, zone) {
    let row = locals[cdt][cdn];
    let selling_price_field = `${zone}_sp`;
    let purchase_price_field = `${zone}_pp_after_tax`;
    let markup_field = `${zone}_mp`;
    let selling_price_after_tax_field = `${zone}_sp_after_tax`;
    let tax_rate_field = `${zone}_tax_rate`;
    let selling_price = flt(row[selling_price_field]);
    let purchase_price = flt(row[purchase_price_field]);
    let tax_rate = flt(row[tax_rate_field]) / 100;
    if (purchase_price > 0) {
        row[markup_field] = ((selling_price - purchase_price) / purchase_price) * 100;
    } else {
        row[markup_field] = 0;
    }
    row[selling_price_after_tax_field] = selling_price * (1 + tax_rate); 
    frm.refresh_field("items");
    recalc_row_and_totals(frm, cdt, cdn);
}
function update_selling_price_from_markup(frm, cdt, cdn, zone) {
    let row = locals[cdt][cdn];
    let markup_field = `${zone}_mp`;
    let purchase_price_field = `${zone}_pp_after_tax`;
    let selling_price_field = `${zone}_sp`;
    let selling_price_after_tax_field = `${zone}_sp_after_tax`;
    let tax_rate_field = `${zone}_tax_rate`;
    let markup = flt(row[markup_field]);
    let purchase_price = flt(row[purchase_price_field]);
    let tax_rate = flt(row[tax_rate_field]) / 100;
    row[selling_price_field] = purchase_price * (1 + (markup / 100));
    row[selling_price_after_tax_field] = row[selling_price_field] * (1 + tax_rate);
    frm.refresh_field("items");
    recalc_row_and_totals(frm, cdt, cdn);
}
function fetch_tax_and_stock_then_recalc(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row.item_code) {
        reset_row_fields(row);
        frm.refresh_field("items");
        recalc_row_and_totals(frm, cdt, cdn);
        return;
    }
    let tax_promises = [
        frappe.xcall ? 
            frappe.xcall('masar_mce.utils.get_tax_for_item', { 
                item_code: row.item_code, 
                category: 'Local Zone' 
            }) :
            frappe.call({ 
                method: 'masar_mce.utils.get_tax_for_item', 
                args: { 
                    item_code: row.item_code, 
                    category: 'Local Zone' 
                } 
            }),
        frappe.xcall ? 
            frappe.xcall('masar_mce.utils.get_tax_for_item', { 
                item_code: row.item_code, 
                category: 'Free Zone' 
            }) :
            frappe.call({ 
                method: 'masar_mce.utils.get_tax_for_item', 
                args: { 
                    item_code: row.item_code, 
                    category: 'Free Zone' 
                } 
            })
    ];
    let stock_promises = [
        frappe.xcall ? 
            frappe.xcall('masar_mce.utils.get_current_stock_value_and_quantity', { 
                item_code: row.item_code, 
                cost_zone: 'Local Zone' 
            }) :
            frappe.call({ 
                method: 'masar_mce.utils.get_current_stock_value_and_quantity', 
                args: { 
                    item_code: row.item_code, 
                    cost_zone: 'Local Zone' 
                } 
            }),
        frappe.xcall ? 
            frappe.xcall('masar_mce.utils.get_current_stock_value_and_quantity', { 
                item_code: row.item_code, 
                cost_zone: 'Free Zone' 
            }) :
            frappe.call({ 
                method: 'masar_mce.utils.get_current_stock_value_and_quantity', 
                args: { 
                    item_code: row.item_code, 
                    cost_zone: 'Free Zone' 
                } 
            })
    ];

    Promise.all([...tax_promises, ...stock_promises])
        .then(results => {
            const local_tax_result = results[0].message !== undefined ? results[0].message : results[0];
            const free_tax_result = results[1].message !== undefined ? results[1].message : results[1];
            const local_stock_result = results[2].message !== undefined ? results[2].message : results[2];
            const free_stock_result = results[3].message !== undefined ? results[3].message : results[3];
            row.local_tax_rate = flt(local_tax_result) * 100;
            row.free_tax_rate = flt(free_tax_result) * 100;
            row.local_curr_stock_value = flt(local_stock_result.stock_value || 0);
            row.local_curr_qty = flt(local_stock_result.quantity || 0);
            row.local_curr_val_rate = flt(local_stock_result.valuation_rate || 0);
            row.free_curr_stock_value = flt(free_stock_result.stock_value || 0);
            row.free_curr_qty = flt(free_stock_result.quantity || 0);
            row.free_curr_cal_rate = flt(free_stock_result.valuation_rate || 0);
            calculate_global_values(row);
            frm.refresh_field("items");
            recalc_row_and_totals(frm, cdt, cdn);
        })
        .catch(err => {
            console.error("Error fetching data:", err);
            fetch_data_fallback(frm, row, cdt, cdn);
        });
}

function fetch_data_fallback(frm, row, cdt, cdn) {
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
                        args: { item_code: row.item_code, cost_zone: 'Local Zone' },
                        callback: function(r3) {
                            const local_stock = r3.message || {};
                            row.local_curr_stock_value = flt(local_stock.stock_value || 0);
                            row.local_curr_qty = flt(local_stock.quantity || 0);
                            row.local_curr_val_rate = flt(local_stock.valuation_rate || 0);
                            
                            frappe.call({
                                method: 'masar_mce.utils.get_current_stock_value_and_quantity',
                                args: { item_code: row.item_code, cost_zone: 'Free Zone' },
                                callback: function(r4) {
                                    const free_stock = r4.message || {};
                                    row.free_curr_stock_value = flt(free_stock.stock_value || 0);
                                    row.free_curr_qty = flt(free_stock.quantity || 0);
                                    row.free_curr_cal_rate = flt(free_stock.valuation_rate || 0);
                                    calculate_global_values(row);
                                    frm.refresh_field("items");
                                    recalc_row_and_totals(frm, cdt, cdn);
                                }
                            });
                        }
                    });
                }
            });
        }
    });
}

function calculate_global_values(row) {
    const local_stock_value = flt(row.local_curr_stock_value);
    const free_stock_value = flt(row.free_curr_stock_value);
    const local_qty = flt(row.local_curr_qty);
    const free_qty = flt(row.free_curr_qty);
    const new_purchase_price = flt(row.new_purchase_price);
    const new_quantity = flt(row.new_quantity);
    const global_current_stock_value = local_stock_value + free_stock_value;
    const global_new_stock_value = global_current_stock_value + (new_purchase_price * new_quantity);
    const total_current_qty = local_qty + free_qty;
    const total_qty_with_new = total_current_qty + new_quantity;
    const global_val_rate = total_qty_with_new > 0 ? 
        global_new_stock_value / total_qty_with_new : 0;
    row.global_curr_stock_value = global_current_stock_value;
    row.global_new_stock_value = global_new_stock_value;
    row.global_val_rate = global_val_rate;
}
function recalc_row_and_totals(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.new_purchase_price = flt(row.new_purchase_price);
    row.new_quantity = flt(row.new_quantity);
    row.local_curr_stock_value = flt(row.local_curr_stock_value);
    row.local_curr_qty = flt(row.local_curr_qty);
    row.free_curr_stock_value = flt(row.free_curr_stock_value);
    row.free_curr_qty = flt(row.free_curr_qty);
    let local_tax_decimal = flt(row.local_tax_rate) / 100.0;
    let free_tax_decimal = flt(row.free_tax_rate) / 100.0;
    row.local_pp_after_tax = flt(row.new_purchase_price) * (1 + local_tax_decimal);
    row.free_pp_after_tax = flt(row.new_purchase_price) * (1 + free_tax_decimal);
    row.local_sp_after_tax = flt(row.local_sp) * (1 + local_tax_decimal);
    row.free_sp_after_tax = flt(row.free_sp) * (1 + free_tax_decimal);
    calculate_global_values(row);  
    frm.refresh_field("items");
    GetTotals(frm);
}
function reset_row_fields(row) {
    row.local_tax_rate = 0;
    row.free_tax_rate = 0;
    row.local_curr_stock_value = 0;
    row.local_curr_qty = 0;
    row.local_curr_val_rate = 0;
    row.free_curr_stock_value = 0;
    row.free_curr_qty = 0;
    row.free_curr_cal_rate = 0;
    row.global_curr_stock_value = 0;
    row.global_new_stock_value = 0;
    row.global_val_rate = 0;
    row.local_pp_after_tax = 0;
    row.free_pp_after_tax = 0;
    row.local_sp = 0;
    row.free_sp = 0;
    row.local_sp_after_tax = 0;
    row.free_sp_after_tax = 0;
    row.local_mp = 0;
    row.free_mp = 0;
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
                    try {
                        // Fetch stock for both zones
                        let [local_stock_info, free_stock_info, tax_local, tax_free] = await Promise.all([
                            frappe.call({
                                method: "masar_mce.utils.get_current_stock_value_and_quantity",
                                args: { item_code: item.item_code, cost_zone: 'Local Zone' }
                            }),
                            frappe.call({
                                method: "masar_mce.utils.get_current_stock_value_and_quantity",
                                args: { item_code: item.item_code, cost_zone: 'Free Zone' }
                            }),
                            frappe.call({
                                method: "masar_mce.utils.get_tax_for_item",
                                args: { item_code: item.item_code, category: 'Local Zone' }
                            }),
                            frappe.call({
                                method: "masar_mce.utils.get_tax_for_item",
                                args: { item_code: item.item_code, category: 'Free Zone' }
                            })
                        ]);
                        let local_tax_rate = flt(tax_local.message) * 100;
                        let free_tax_rate = flt(tax_free.message) * 100;
                        let local_stock = local_stock_info.message || {};
                        let free_stock = free_stock_info.message || {};
                        let new_purchase_price = flt(item.custom_purchase_price || item.rate || 0);
                        let new_quantity = flt(item.custom_qty || 0);
                        let markup_percentage = flt(item.custom_markup_percentage || 0);
                        let local_pp_after_tax = flt(new_purchase_price) * (1 + flt(tax_local.message));
                        let free_pp_after_tax = flt(new_purchase_price) * (1 + flt(tax_free.message));
                        let local_sp = flt(local_pp_after_tax) * (1 + markup_percentage / 100);
                        let free_sp = flt(free_pp_after_tax) * (1 + markup_percentage / 100);
                        let global_curr_stock_value = flt(local_stock.stock_value || 0) + flt(free_stock.stock_value || 0);
                        let total_curr_qty = flt(local_stock.quantity || 0) + flt(free_stock.quantity || 0);
                        let global_new_stock_value = global_curr_stock_value + (new_purchase_price * new_quantity);
                        let total_qty = total_curr_qty + new_quantity;
                        let global_val_rate = total_qty > 0 ? global_new_stock_value / total_qty : 0;
                        data.push({
                            item_code: item.item_code,
                            item_name: item.item_name,
                            new_purchase_price: new_purchase_price,
                            new_quantity: new_quantity,
                            local_tax_rate: local_tax_rate,
                            free_tax_rate: free_tax_rate,
                            local_pp_after_tax: local_pp_after_tax,
                            free_pp_after_tax: free_pp_after_tax,
                            local_mp: markup_percentage,
                            free_mp: markup_percentage,
                            local_sp: local_sp,
                            free_sp: free_sp,
                            local_sp_after_tax: flt(local_sp) * (1 + flt(tax_local.message)),
                            free_sp_after_tax: flt(free_sp) * (1 + flt(tax_free.message)),
                            local_curr_qty: flt(local_stock.quantity || 0),
                            local_curr_stock_value: flt(local_stock.stock_value || 0),
                            free_curr_qty: flt(free_stock.quantity || 0),
                            free_curr_stock_value: flt(free_stock.stock_value || 0)
                        });
                    } catch (error) {
                        console.error("Error fetching item data:", error);
                    }
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
                                { fieldname: "local_curr_stock_value", label: "Local Stock Value", fieldtype: "Currency", read_only: 1, width: 140, in_list_view: 1 },
                                { fieldname: "local_curr_qty", label: "Local Qty", fieldtype: "Float", read_only: 1, width: 100, in_list_view: 1 },
                                { fieldname: "free_curr_stock_value", label: "Free Stock Value", fieldtype: "Currency", read_only: 1, width: 140, in_list_view: 1 },
                                { fieldname: "free_curr_qty", label: "Free Qty", fieldtype: "Float", read_only: 1, width: 100, in_list_view: 1 },
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
                        selected_rows.forEach(async (row) => {
                            if (!frm.doc.items.some(i => i.item_code === row.item_code)) {
                                let [local_stock_info, free_stock_info] = await Promise.all([
                                    frappe.call({
                                        method: "masar_mce.utils.get_current_stock_value_and_quantity",
                                        args: { item_code: row.item_code, cost_zone: 'Local Zone' }
                                    }),
                                    frappe.call({
                                        method: "masar_mce.utils.get_current_stock_value_and_quantity",
                                        args: { item_code: row.item_code, cost_zone: 'Free Zone' }
                                    })
                                ]);

                                let local_stock = local_stock_info.message || {};
                                let free_stock = free_stock_info.message || {};
                                let new_row = frm.add_child("items");
                                new_row.item_code = row.item_code;
                                new_row.item_name = row.item_name;
                                new_row.local_curr_qty = flt(local_stock.quantity || 0);
                                new_row.local_curr_stock_value = flt(local_stock.stock_value || 0);
                                new_row.local_curr_val_rate = flt(local_stock.valuation_rate || 0);
                                new_row.free_curr_qty = flt(free_stock.quantity || 0);
                                new_row.free_curr_stock_value = flt(free_stock.stock_value || 0);
                                new_row.free_curr_cal_rate = flt(free_stock.valuation_rate || 0);
                                new_row.new_purchase_price = row.new_purchase_price;
                                new_row.new_quantity = row.new_quantity;
                                new_row.local_tax_rate = row.local_tax_rate;
                                new_row.free_tax_rate = row.free_tax_rate;
                                new_row.local_pp_after_tax = row.local_pp_after_tax;
                                new_row.free_pp_after_tax = row.free_pp_after_tax;
                                new_row.local_mp = flt(row.local_mp || 0);
                                new_row.free_mp = flt(row.free_mp || 0);
                                new_row.local_sp = row.local_sp;
                                new_row.free_sp = row.free_sp;
                                new_row.local_sp_after_tax = flt(row.local_sp_after_tax);
                                new_row.free_sp_after_tax = flt(row.free_sp_after_tax);
                                calculate_global_values(new_row);
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