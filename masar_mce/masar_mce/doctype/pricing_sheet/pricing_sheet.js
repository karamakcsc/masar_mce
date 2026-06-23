/******************************************************************
 * PRICING SHEET – AFTER TAX BASED PRICING
 * Corrected: local_sp = before tax, local_sp_after_tax = after tax
 * Markup formula: (sp - pp_after_tax) / pp_after_tax * 100
 ******************************************************************/

frappe.ui.form.on("Pricing Sheet", {
    refresh(frm) {
        set_item_query(frm);
        GetItemsDialog(frm);
        GetLastSync(frm);
        if (frm.doc.from_agreement) {
            frm.set_read_only();
            frm.disable_save();
            frm.dashboard && frm.dashboard.set_headline &&
                frm.dashboard.set_headline(
                    __("This Pricing Sheet is auto-generated from Supplier Agreement and is read-only.")
                );
        }
    },
    blanket_order(frm) {
        set_item_query(frm);
        GetItemsDialog(frm);
    },
    setup(frm) {
        set_item_query(frm);
        GetItemsDialog(frm);
        GetLastSync(frm);
    },
    pricing_type(frm) {
        if (frm.doc.items) {
            frm.doc.items.forEach((row, idx) => {
                const cdt = "Pricing Sheet Items";
                const cdn = row.name;
                
                if (frm.doc.pricing_type === "Buying Price Basis") {
                    calculateBuyingPriceBasis(frm, cdt, cdn);
                } else if (frm.doc.pricing_type === "Selling Price Basis") {
                    // For selling price basis, start with local zone
                    if (row.local_sp) {
                        calculateSellingPriceBasisFromSellingBeforeTax(frm, cdt, cdn, 'local');
                    }
                }
                
                calculate_global_values(row);
            });
            frm.refresh_field("items");
            GetTotals(frm);
        }
    },
    onload: function(frm) {
        frm.get_field('items').grid.cannot_add_rows = true;
}
});

frappe.ui.form.on("Pricing Sheet Items", {
    item_code(frm, cdt, cdn) {
        fetch_tax_and_stock_then_recalc(frm, cdt, cdn);
    },
    
    // COMMON FIELDS
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
    items_remove(frm) {
        GetTotals(frm);
    },
    
    // BUYING PRICE BASIS - Purchase Price
    new_purchase_price(frm, cdt, cdn) {
        if (frm.doc.pricing_type === "Buying Price Basis") {
            calculateBuyingPriceBasis(frm, cdt, cdn);
        } else if (frm.doc.pricing_type === "Selling Price Basis") {
            // For selling price basis, recalculate markup based on new purchase price
            recalculateMarkupFromPurchasePrice(frm, cdt, cdn);
        }
        recalc_row_and_totals(frm, cdt, cdn);
    },
    
    // BUYING PRICE BASIS - Local Zone
    local_mp(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        
        if (frm.doc.pricing_type === "Buying Price Basis") {
            // Calculate selling before tax and after tax from markup
            calculateSellingFromMarkupForZone(frm, cdt, cdn, 'local');
        } else if (frm.doc.pricing_type === "Selling Price Basis") {
            // Calculate purchase after tax and purchase price from markup
            calculatePurchaseFromMarkupForZone(frm, cdt, cdn, 'local');
        }
        recalc_row_and_totals(frm, cdt, cdn);
    },
    
    local_sp(frm, cdt, cdn) {
        // Calculate selling after tax from selling before tax
        calculateSellingAfterTaxFromSellingBeforeTax(frm, cdt, cdn, 'local');

        if (frm.doc.pricing_type === "Buying Price Basis") {
            calculateMarkupFromSellingBeforeTax(frm, cdt, cdn, 'local');
        } else if (frm.doc.pricing_type === "Selling Price Basis") {
            calculateSellingPriceBasisFromSellingBeforeTax(frm, cdt, cdn, 'local');
        }

        recalc_row_and_totals(frm, cdt, cdn);
    },
    
    local_sp_after_tax(frm, cdt, cdn) {
        // Calculate selling before tax from selling after tax
        calculateSellingBeforeTaxFromSellingAfterTax(frm, cdt, cdn, 'local');
        
        if (frm.doc.pricing_type === "Buying Price Basis") {
            calculateMarkupFromSellingBeforeTax(frm, cdt, cdn, 'local');
        } else if (frm.doc.pricing_type === "Selling Price Basis") {
            calculateSellingPriceBasisFromSellingBeforeTax(frm, cdt, cdn, 'local');
        }
        recalc_row_and_totals(frm, cdt, cdn);
    },
    
    // BUYING PRICE BASIS - Free Zone
    free_mp(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        
        if (frm.doc.pricing_type === "Buying Price Basis") {
            // Calculate selling before tax and after tax from markup
            calculateSellingFromMarkupForZone(frm, cdt, cdn, 'free');
        } else if (frm.doc.pricing_type === "Selling Price Basis") {
            // For selling price basis, free zone only affects free zone values
            calculateFreeZoneFromMarkup(frm, cdt, cdn);
        }
        recalc_row_and_totals(frm, cdt, cdn);
    },
    
    free_sp(frm, cdt, cdn) {
        calculateSellingAfterTaxFromSellingBeforeTax(frm, cdt, cdn, 'free');

        if (frm.doc.pricing_type === "Buying Price Basis") {
            calculateMarkupFromSellingBeforeTax(frm, cdt, cdn, 'free');
        } else if (frm.doc.pricing_type === "Selling Price Basis") {
            calculateFreeZoneFromSellingBeforeTax(frm, cdt, cdn);
        }

        recalc_row_and_totals(frm, cdt, cdn);
    },
    
    free_sp_after_tax(frm, cdt, cdn) {
        calculateSellingBeforeTaxFromSellingAfterTax(frm, cdt, cdn, 'free');
        
        if (frm.doc.pricing_type === "Buying Price Basis") {
            calculateMarkupFromSellingBeforeTax(frm, cdt, cdn, 'free');
        } else if (frm.doc.pricing_type === "Selling Price Basis") {
            calculateFreeZoneFromSellingBeforeTax(frm, cdt, cdn);
        }
        recalc_row_and_totals(frm, cdt, cdn);
    }
});

/******************************************************************
 * BUYING PRICE BASIS FUNCTIONS
 ******************************************************************/

function calculateBuyingPriceBasis(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (!row.new_purchase_price) {
        resetPurchaseAndSelling(row);
        return;
    }
    
    let local_tax_decimal = flt(row.local_tax_rate) / 100.0;
    let free_tax_decimal = flt(row.free_tax_rate) / 100.0;
    
    // 1. Calculate purchase after tax for both zones
    row.local_pp_after_tax = flt(row.new_purchase_price) * (1 + local_tax_decimal);
    row.free_pp_after_tax = flt(row.new_purchase_price) * (1 + free_tax_decimal);
    
    // 2. Calculate selling before tax from markup for both zones
    // Using new formula: sp = pp_after_tax * (1 + markup/100)
    if (flt(row.local_mp) || flt(row.local_mp) === 0) {
        row.local_sp = row.local_pp_after_tax * (1 + flt(row.local_mp) / 100);
    } else {
        row.local_sp = row.local_pp_after_tax;
    }
    
    if (flt(row.free_mp) || flt(row.free_mp) === 0) {
        row.free_sp = row.free_pp_after_tax * (1 + flt(row.free_mp) / 100);
    } else {
        row.free_sp = row.free_pp_after_tax;
    }
    
    // 3. Calculate selling after tax (for tax calculation)
    if (flt(row.local_sp)) {
        row.local_sp_after_tax = flt(row.local_sp) * (1 + local_tax_decimal);
    } else {
        row.local_sp_after_tax = 0;
    }
    
    if (flt(row.free_sp)) {
        row.free_sp_after_tax = flt(row.free_sp) * (1 + free_tax_decimal);
    } else {
        row.free_sp_after_tax = 0;
    }
    
    frm.refresh_field("items");
}

function calculateSellingFromMarkupForZone(frm, cdt, cdn, zone) {
    let row = locals[cdt][cdn];
    let pp_after_tax_field = `${zone}_pp_after_tax`;
    let markup_field = `${zone}_mp`;
    let sp_field = `${zone}_sp`;
    let sp_after_tax_field = `${zone}_sp_after_tax`;
    let tax_field = `${zone}_tax_rate`;
    
    let purchase_after_tax = flt(row[pp_after_tax_field]);
    let markup = flt(row[markup_field]);
    let tax_decimal = flt(row[tax_field]) / 100.0;
    
    if (purchase_after_tax) {
        // Calculate selling before tax from markup
        // Using formula: sp = pp_after_tax * (1 + markup/100)
        if (markup || markup === 0) {
            row[sp_field] = purchase_after_tax * (1 + markup / 100);
        } else {
            row[sp_field] = purchase_after_tax;
        }
        
        // Calculate selling after tax (for display)
        if (flt(row[sp_field])) {
            row[sp_after_tax_field] = flt(row[sp_field]) * (1 + tax_decimal);
        } else {
            row[sp_after_tax_field] = 0;
        }
    }
    
    frm.refresh_field("items");
}

function calculateMarkupFromSellingBeforeTax(frm, cdt, cdn, zone) {
    let row = locals[cdt][cdn];
    let pp_after_tax_field = `${zone}_pp_after_tax`;
    let markup_field = `${zone}_mp`;
    let sp_field = `${zone}_sp`;
    
    let selling_before_tax = flt(row[sp_field]);
    let purchase_after_tax = flt(row[pp_after_tax_field]);
    
    if (selling_before_tax && purchase_after_tax) {
        // Calculate markup using the formula: (sp - pp_after_tax) / pp_after_tax * 100
        if (purchase_after_tax !== 0) {
            row[markup_field] = ((selling_before_tax - purchase_after_tax) / purchase_after_tax) * 100;
        } else if (selling_before_tax > 0) {
            // If purchase after tax is 0 but selling is positive, markup is infinite
            row[markup_field] = 100;
        } else {
            row[markup_field] = 0;
        }
    } else if (selling_before_tax && !purchase_after_tax) {
        // If no purchase after tax, set markup to 0
        row[markup_field] = 0;
    }
    
    frm.refresh_field("items");
}

/******************************************************************
 * SELLING PRICE BASIS FUNCTIONS
 ******************************************************************/

function calculateSellingPriceBasisFromSellingBeforeTax(frm, cdt, cdn, zone) {
    let row = locals[cdt][cdn];
    
    if (zone !== 'local') return; // Only local zone drives purchase price
    
    let local_tax_decimal = flt(row.local_tax_rate) / 100.0;
    let selling_before_tax = flt(row.local_sp);
    let markup = flt(row.local_mp);
    
    if (selling_before_tax) {
        // 1. Calculate selling after tax
        row.local_sp_after_tax = selling_before_tax * (1 + local_tax_decimal);
        
        if (markup || markup === 0) {
            if (markup !== -100) {
                // 2. Calculate purchase after tax from selling before tax and markup
                // Formula: pp_after_tax = sp / (1 + markup/100)
                row.local_pp_after_tax = selling_before_tax * (1 - markup / 100);
                
                // 3. Calculate purchase price (before tax)
                row.new_purchase_price = row.local_pp_after_tax / (1 + local_tax_decimal);
            } else {
                // If markup is -100%, purchase after tax is 0
                row.local_pp_after_tax = 0;
                row.new_purchase_price = 0;
            }
        } else {
            // If no markup, selling before tax = purchase after tax
            row.local_pp_after_tax = selling_before_tax;
            row.new_purchase_price = selling_before_tax / (1 + local_tax_decimal);
        }
        
        // 4. Calculate free zone based on new purchase price
        calculateFreeZoneFromPurchasePrice(frm, cdt, cdn);
    }
    
    frm.refresh_field("items");
}

function calculatePurchaseFromMarkupForZone(frm, cdt, cdn, zone) {
    let row = locals[cdt][cdn];
    
    if (zone !== 'local') return; // Only local zone affects purchase price
    
    let local_tax_decimal = flt(row.local_tax_rate) / 100.0;
    let selling_before_tax = flt(row.local_sp);
    let markup = flt(row.local_mp);
    
    if (selling_before_tax && (markup || markup === 0)) {
        // 1. Calculate purchase after tax from selling before tax and markup
        if (markup !== -100) {
            row.local_pp_after_tax = selling_before_tax * (1 - markup / 100);
            
            // 2. Calculate purchase price (before tax)
            row.new_purchase_price = row.local_pp_after_tax / (1 + local_tax_decimal);
        } else {
            row.local_pp_after_tax = 0;
            row.new_purchase_price = 0;
        }
        
        // 3. Calculate selling after tax
        row.local_sp_after_tax = selling_before_tax * (1 + local_tax_decimal);
        
        // 4. Calculate free zone based on new purchase price
        calculateFreeZoneFromPurchasePrice(frm, cdt, cdn);
    }
    
    frm.refresh_field("items");
}

function recalculateMarkupFromPurchasePrice(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let local_tax_decimal = flt(row.local_tax_rate) / 100.0;
    let selling_before_tax = flt(row.local_sp);
    
    if (selling_before_tax && row.new_purchase_price) {
        // 1. Calculate purchase after tax
        row.local_pp_after_tax = flt(row.new_purchase_price) * (1 + local_tax_decimal);
        
        // 2. Calculate markup using the formula: (sp - pp_after_tax) / pp_after_tax * 100
        if (row.local_pp_after_tax > 0) {
            row.local_mp = ((selling_before_tax - row.local_pp_after_tax) / row.local_pp_after_tax) * 100;
        } else if (selling_before_tax > 0) {
            // If purchase after tax is 0 but selling is positive, markup is infinite
            row.local_mp = 100;
        } else {
            row.local_mp = 0;
        }
        
        // 3. Calculate selling after tax
        row.local_sp_after_tax = selling_before_tax * (1 + local_tax_decimal);
        
        // 4. Calculate free zone based on new purchase price
        calculateFreeZoneFromPurchasePrice(frm, cdt, cdn);
    }
    
    frm.refresh_field("items");
}

function calculateFreeZoneFromPurchasePrice(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (!row.new_purchase_price) return;
    
    let free_tax_decimal = flt(row.free_tax_rate) / 100.0;
    let markup = flt(row.free_mp);
    
    // 1. Calculate purchase after tax for free zone
    row.free_pp_after_tax = flt(row.new_purchase_price) * (1 + free_tax_decimal);
    
    // 2. Calculate selling before tax from markup
    // Using formula: sp = pp_after_tax * (1 + markup/100)
    if (markup || markup === 0) {
        if (markup !== -100) {
            row.free_sp = row.free_pp_after_tax * (1 + markup / 100);
        } else {
            row.free_sp = 0;
        }
    } else {
        row.free_sp = row.free_pp_after_tax;
    }
    
    // 3. Calculate selling after tax (for display)
    if (flt(row.free_sp)) {
        row.free_sp_after_tax = flt(row.free_sp) * (1 + free_tax_decimal);
    } else {
        row.free_sp_after_tax = 0;
    }
    
    frm.refresh_field("items");
}

function calculateFreeZoneFromMarkup(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (!row.new_purchase_price) return;
    
    let free_tax_decimal = flt(row.free_tax_rate) / 100.0;
    let markup = flt(row.free_mp);
    
    // 1. Calculate purchase after tax for free zone
    row.free_pp_after_tax = flt(row.new_purchase_price) * (1 + free_tax_decimal);
    
    // 2. Calculate selling before tax from markup
    // Using formula: sp = pp_after_tax * (1 + markup/100)
    if (markup || markup === 0) {
        if (markup !== -100) {
            row.free_sp = row.free_pp_after_tax * (1 + markup / 100);
        } else {
            row.free_sp = 0;
        }
    } else {
        row.free_sp = row.free_pp_after_tax;
    }
    
    // 3. Calculate selling after tax (for display)
    if (flt(row.free_sp)) {
        row.free_sp_after_tax = flt(row.free_sp) * (1 + free_tax_decimal);
    } else {
        row.free_sp_after_tax = 0;
    }
    
    frm.refresh_field("items");
}

function calculateFreeZoneFromSellingBeforeTax(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (!row.new_purchase_price) return;
    
    let free_tax_decimal = flt(row.free_tax_rate) / 100.0;
    let selling_before_tax = flt(row.free_sp);
    
    if (selling_before_tax) {
        // 1. Calculate selling after tax
        row.free_sp_after_tax = selling_before_tax * (1 + free_tax_decimal);
        
        // 2. Calculate purchase after tax (should already be set from purchase price)
        if (!row.free_pp_after_tax) {
            row.free_pp_after_tax = flt(row.new_purchase_price) * (1 + free_tax_decimal);
        }
        
        // 3. Calculate markup using the formula: (sp - pp_after_tax) / pp_after_tax * 100
        if (row.free_pp_after_tax > 0) {
            row.free_mp = ((selling_before_tax - row.free_pp_after_tax) / row.free_pp_after_tax) * 100;
        } else if (selling_before_tax > 0) {
            // If purchase after tax is 0 but selling is positive, markup is infinite
            row.free_mp = 100;
        } else {
            row.free_mp = 0;
        }
    }
    
    frm.refresh_field("items");
}

/******************************************************************
 * COMMON FUNCTIONS
 ******************************************************************/

function resetPurchaseAndSelling(row) {
    row.local_pp_after_tax = 0;
    row.free_pp_after_tax = 0;
    row.local_sp = 0;
    row.free_sp = 0;
    row.local_sp_after_tax = 0;
    row.free_sp_after_tax = 0;
    row.local_mp = 0;
    row.free_mp = 0;
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
        frappe.call({ 
            method: 'masar_mce.utils.get_tax_for_item', 
            args: { 
                item_code: row.item_code, 
                category: 'Local Zone' 
            } 
        }),
        frappe.call({ 
            method: 'masar_mce.utils.get_tax_for_item', 
            args: { 
                item_code: row.item_code, 
                category: 'Free Zone' 
            } 
        })
    ];  
    
    let stock_promises = [
        frappe.call({ 
            method: 'masar_mce.utils.get_current_stock_value_and_quantity', 
            args: { 
                item_code: row.item_code, 
                cost_zone: 'Local Zone' 
            } 
        }),
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
            
            if (frm.doc.pricing_type === "Buying Price Basis") {
                calculateBuyingPriceBasis(frm, cdt, cdn);
            } else if (frm.doc.pricing_type === "Selling Price Basis") {
                // For Selling Price Basis, calculate from selling before tax if exists
                if (row.local_sp) {
                    calculateSellingPriceBasisFromSellingBeforeTax(frm, cdt, cdn, 'local');
                }
            }
            
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
                                    
                                    if (frm.doc.pricing_type === "Buying Price Basis") {
                                        calculateBuyingPriceBasis(frm, cdt, cdn);
                                    } else if (frm.doc.pricing_type === "Selling Price Basis") {
                                        if (row.local_sp) {
                                            calculateSellingPriceBasisFromSellingBeforeTax(frm, cdt, cdn, 'local');
                                        }
                                    }
                                    
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
    
    // Calculate purchase after tax if not set
    let local_tax_decimal = flt(row.local_tax_rate) / 100.0;
    let free_tax_decimal = flt(row.free_tax_rate) / 100.0;
    
    if (!row.local_pp_after_tax && row.new_purchase_price) {
        row.local_pp_after_tax = flt(row.new_purchase_price) * (1 + local_tax_decimal);
    }
    
    if (!row.free_pp_after_tax && row.new_purchase_price) {
        row.free_pp_after_tax = flt(row.new_purchase_price) * (1 + free_tax_decimal);
    }
    
    // Calculate selling after tax if selling before tax exists
    if (row.local_sp && !row.local_sp_after_tax) {
        row.local_sp_after_tax = flt(row.local_sp) * (1 + local_tax_decimal);
    }
    
    if (row.free_sp && !row.free_sp_after_tax) {
        row.free_sp_after_tax = flt(row.free_sp) * (1 + free_tax_decimal);
    }
    
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
    row.new_purchase_price = 0;
}

function GetTotals(frm) {
    let new_total_quantity = 0;
    let local_sa = 0;
    let free_sa = 0;
    let new_purchase_amount = 0;
    
    (frm.doc.items || []).forEach(row => {
        new_total_quantity += flt(row.new_quantity);
        // Use selling before tax for totals
        local_sa += flt(row.new_quantity) * flt(row.local_sp);
        free_sa += flt(row.new_quantity) * flt(row.free_sp);
        new_purchase_amount += flt(row.new_quantity) * flt(row.new_purchase_price);
    });

    frm.set_value("new_total_quantity", new_total_quantity);
    frm.set_value("local_sa", local_sa);
    frm.set_value("free_sa", free_sa);
    frm.set_value("new_purchase_amount", new_purchase_amount);

    frm.refresh_fields();
}

function calculateSellingAfterTaxFromSellingBeforeTax(frm, cdt, cdn, zone) {
    let row = locals[cdt][cdn];

    let tax_rate = flt(row[`${zone}_tax_rate`]) / 100;
    let selling_before_tax = flt(row[`${zone}_sp`]);

    if (!selling_before_tax) {
        row[`${zone}_sp_after_tax`] = 0;
        return;
    }

    // selling after tax = selling before tax + tax
    row[`${zone}_sp_after_tax`] = selling_before_tax * (1 + tax_rate);
}

function calculateSellingBeforeTaxFromSellingAfterTax(frm, cdt, cdn, zone) {
    let row = locals[cdt][cdn];

    let tax_rate = flt(row[`${zone}_tax_rate`]) / 100;
    let selling_after_tax = flt(row[`${zone}_sp_after_tax`]);

    if (!selling_after_tax) {
        row[`${zone}_sp`] = 0;
        return;
    }

    // selling before tax = selling after tax / (1 + tax_rate)
    row[`${zone}_sp`] = selling_after_tax / (1 + tax_rate);
}

// Update GetItemsDialog to use correct field names
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
                
                if (remaining_items.length === 0) {
                    frappe.msgprint("All items from this Supplier Agreement are already added.");
                    return;
                }
                
                let data = [];
                for (let item of remaining_items) {
                    try {
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
                        
                        let local_tax = flt(tax_local.message);
                        let free_tax = flt(tax_free.message);
                        let local_tax_rate = local_tax * 100;
                        let free_tax_rate = free_tax * 100;
                        
                        let local_stock = local_stock_info.message || {};
                        let free_stock = free_stock_info.message || {};
                        let new_purchase_price = flt(item.custom_purchase_price || item.rate || 0);
                        let new_quantity = flt(item.custom_qty || 0);
                        let markup_percentage = flt(item.custom_markup_percentage || 0);
                        
                        let local_pp_after_tax, free_pp_after_tax, local_sp_after_tax, free_sp_after_tax, local_sp, free_sp;
                        
                        // Calculate using the correct field names
                        if (frm.doc.pricing_type === "Buying Price Basis") {
                            // Buying Price Basis
                            local_pp_after_tax = new_purchase_price * (1 + local_tax);
                            free_pp_after_tax = new_purchase_price * (1 + free_tax);
                            local_sp = local_pp_after_tax * (1 + markup_percentage / 100);
                            free_sp = free_pp_after_tax * (1 + markup_percentage / 100);
                            local_sp_after_tax = local_sp * (1 + local_tax);
                            free_sp_after_tax = free_sp * (1 + free_tax);
                        } else {
                            // Selling Price Basis
                            let selling_before_tax = flt(item.custom_selling_price_before_tax || 0);
                            
                            if (selling_before_tax) {
                                local_sp = selling_before_tax;
                                free_sp = selling_before_tax;
                                
                                if (markup_percentage && markup_percentage !== -100) {
                                    local_pp_after_tax = selling_before_tax * (1 - markup_percentage / 100);
                                    free_pp_after_tax = selling_before_tax * (1 - markup_percentage / 100);
                                    new_purchase_price = local_pp_after_tax / (1 + local_tax);
                                } else if (markup_percentage === -100) {
                                    local_pp_after_tax = 0;
                                    free_pp_after_tax = 0;
                                    new_purchase_price = 0;
                                } else {
                                    local_pp_after_tax = selling_before_tax;
                                    free_pp_after_tax = selling_before_tax;
                                    new_purchase_price = selling_before_tax / (1 + local_tax);
                                }
                                
                                local_sp_after_tax = selling_before_tax * (1 + local_tax);
                                free_sp_after_tax = selling_before_tax * (1 + free_tax);
                            } else {
                                // Calculate from purchase price
                                local_pp_after_tax = new_purchase_price * (1 + local_tax);
                                free_pp_after_tax = new_purchase_price * (1 + free_tax);
                                local_sp = local_pp_after_tax * (1 + markup_percentage / 100);
                                free_sp = free_pp_after_tax * (1 + markup_percentage / 100);
                                local_sp_after_tax = local_sp * (1 + local_tax);
                                free_sp_after_tax = free_sp * (1 + free_tax);
                            }
                        }
                        
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
                            local_sp_after_tax: local_sp_after_tax, // After tax
                            free_sp_after_tax: free_sp_after_tax, // After tax
                            local_sp: local_sp, // Before tax
                            free_sp: free_sp, // Before tax
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
                            data: data,
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
                                { fieldname: "local_sp", label: "Local SP (Before Tax)", fieldtype: "Currency", width: 120, in_list_view: 1 },
                                { fieldname: "local_sp_after_tax", label: "Local SP (After Tax)", fieldtype: "Currency", read_only: 1, width: 160, in_list_view: 1 },
                                { fieldname: "free_sp", label: "Free SP (Before Tax)", fieldtype: "Currency", width: 120, in_list_view: 1 },
                                { fieldname: "free_sp_after_tax", label: "Free SP (After Tax)", fieldtype: "Currency", read_only: 1, width: 160, in_list_view: 1 }
                            ]
                        }
                    ],
                    primary_action_label: __("Add Selected Items"),
                    primary_action: () => {
                        const selected_rows = dialog.fields_dict.items_table.grid.get_selected_children();
                        let rowsAdded = false;
                        
                        selected_rows.forEach(async (row) => {
                            if (!frm.doc.items.some(i => i.item_code === row.item_code)) {
                                rowsAdded = true;
                                
                                let new_row = frm.add_child("items");
                                new_row.item_code = row.item_code;
                                new_row.item_name = row.item_name;
                                new_row.new_purchase_price = row.new_purchase_price;
                                new_row.new_quantity = row.new_quantity;
                                new_row.local_tax_rate = row.local_tax_rate;
                                new_row.free_tax_rate = row.free_tax_rate;
                                new_row.local_pp_after_tax = row.local_pp_after_tax;
                                new_row.free_pp_after_tax = row.free_pp_after_tax;
                                new_row.local_mp = flt(row.local_mp || 0);
                                new_row.free_mp = flt(row.free_mp || 0);
                                new_row.local_sp = flt(row.local_sp);
                                new_row.free_sp = flt(row.free_sp);
                                new_row.local_sp_after_tax = flt(row.local_sp_after_tax);
                                new_row.free_sp_after_tax = flt(row.free_sp_after_tax);
                                new_row.local_curr_qty = row.local_curr_qty;
                                new_row.local_curr_stock_value = row.local_curr_stock_value;
                                new_row.free_curr_qty = row.free_curr_qty;
                                new_row.free_curr_stock_value = row.free_curr_stock_value;
                                new_row.local_curr_val_rate = row.local_curr_stock_value > 0 && row.local_curr_qty > 0 ? 
                                    row.local_curr_stock_value / row.local_curr_qty : 0;
                                new_row.free_curr_cal_rate = row.free_curr_stock_value > 0 && row.free_curr_qty > 0 ? 
                                    row.free_curr_stock_value / row.free_curr_qty : 0;
                                
                                calculate_global_values(new_row);
                            }
                        });
                        
                        if (rowsAdded) {
                            frm.refresh_field("items");
                            GetTotals(frm);
                            if (frm.fields_dict["items"] && frm.fields_dict["items"].grid) {
                                frm.fields_dict["items"].grid.refresh();
                            }
                        }
                        
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