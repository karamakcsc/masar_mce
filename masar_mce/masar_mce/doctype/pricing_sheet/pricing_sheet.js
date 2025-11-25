// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

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
    }, 
});
frappe.ui.form.on("Pricing Sheet Items", {
    item_code(frm , cdt , cdn) {
        GetTaxRate(frm , cdt , cdn);
        GetCurrentPriceAndQuantity(frm , cdt , cdn);
    }, 
    rate(frm , cdt , cdn) { 
        CalculateSellingPrice(frm, cdt, cdn);
        CalculateMarkupPercentage(frm, cdt, cdn);
        CalculateRateAfterTax(frm, cdt, cdn);
        GetTotals(frm);
    },
    markup_percentage(frm, cdt, cdn) {
        CalculateSellingPrice(frm, cdt, cdn);
        CalculateSellingPriceAfterTax(frm, cdt, cdn);
        GetTotals(frm);
    },
    selling_price(frm, cdt, cdn) {
        CalculateMarkupPercentage(frm, cdt, cdn);
        CalculateSellingPriceAfterTax(frm, cdt, cdn);
        GetTotals(frm);
    },
    items_remove(frm) {
        GetTotals(frm);
    },
    current_stock_value(frm, cdt, cdn) {
        CalculateSellingPrice(frm, cdt, cdn);
        CalculateMarkupPercentage(frm, cdt, cdn);
        CalculateRateAfterTax(frm, cdt, cdn);
        GetTotals(frm);
    }, 
    current_quantity(frm, cdt, cdn) {
        CalculateSellingPrice(frm, cdt, cdn);
        CalculateMarkupPercentage(frm, cdt, cdn);
        CalculateRateAfterTax(frm, cdt, cdn);
        GetTotals(frm);
    }, 
    new_purchase_price(frm, cdt, cdn) {
        CalculatePurchasePrice(frm, cdt, cdn);
        CalculateSellingPrice(frm, cdt, cdn);
        CalculateMarkupPercentage(frm, cdt, cdn);
        CalculateRateAfterTax(frm, cdt, cdn);
        GetTotals(frm);
    }, 
    new_quantity(frm, cdt, cdn) {
        CalculatePurchasePrice(frm, cdt, cdn);
        CalculateSellingPrice(frm, cdt, cdn);
        CalculateMarkupPercentage(frm, cdt, cdn);
        CalculateRateAfterTax(frm, cdt, cdn);
        GetTotals(frm);
    }, 
});
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

function GetTaxRate(frm , cdt , cdn){
    let row = locals[cdt][cdn]; 
    if (row.item_code) { 
        frappe.call({
            method : 'masar_mce.utils.get_tax_for_item' , 
            args :{
                item_code : row.item_code
            } , 
            callback: function(r) { 
                row.tax_rate = flt(r.message) * 100 ; 
                row.rate_after_tax = flt(row.rate) + flt(row.rate) * flt(r.message);
                row.selling_price_after_tax = flt(row.selling_price) + flt(row.selling_price) * flt(r.message); 
                frm.refresh_field("items");
            }
        })
    }
}
function GetCurrentPriceAndQuantity(frm , cdt , cdn){
    let row = locals[cdt][cdn]; 
    frappe.call({
        doc: frm.doc, 
        method:'get_stock_value_and_quantity', 
        args:{
            row : row
        }, 
        callback: function(r) {
            row.current_stock_value = r.message.value;
            row.current_quantity = r.message.quantity;
            frm.refresh_field("items");
        }
    });
        
}
function CalculateRateAfterTax(frm , cdt , cdn) {
    let row = locals[cdt][cdn]; 
    if (row.item_code) { 
        frappe.call({
            method : 'masar_mce.utils.get_tax_for_item' , 
            args :{
                item_code : row.item_code
            } , 
            callback: function(r) { 
                row.rate_after_tax = flt(row.rate) + flt(row.rate) * flt(r.message);
                frm.refresh_field("items");
            }
        })
    }
}
function CalculateSellingPriceAfterTax(frm , cdt , cdn) {
    let row = locals[cdt][cdn]; 
    if (row.item_code) { 
        frappe.call({
            method : 'masar_mce.utils.get_tax_for_item' , 
            args :{
                item_code : row.item_code
            } , 
            callback: function(r) { 
                row.rate_after_tax = flt(row.rate) + flt(row.rate) * flt(r.message);
                frm.refresh_field("items");
            }
        })
    }
}
function CalculateSellingPrice(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (flt(row.rate) && flt(row.markup_percentage)) {
        row.selling_price = flt(row.rate) + (flt(row.rate) * flt(row.markup_percentage) / 100);
    } else {
        row.selling_price = 0;
    }
    frm.refresh_field("items");
}
function CalculateMarkupPercentage(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (flt(row.rate) && flt(row.selling_price)) {
        row.markup_percentage = ((flt(row.selling_price) - flt(row.rate)) / flt(row.rate)) * 100;
    } else {
        row.markup_percentage = 0;
    }
    frm.refresh_field("items");
}
function GetTotals(frm) {
    let total_rate = 0;
    let total_rate_after_tax = 0;
    let total_selling_price = 0;
    let total_selling_price_after_tax = 0;

    (frm.doc.items || []).forEach(row => {
        total_rate += flt(row.rate);
        total_rate_after_tax += flt(row.rate_after_tax);
        total_selling_price += flt(row.selling_price);
        total_selling_price_after_tax += flt(row.selling_price_after_tax);
    });

    frm.set_value("total_purchase_price", total_rate);
    frm.set_value("total_purchase_price_after_tax", total_rate_after_tax);
    frm.set_value("total_selling_price", total_selling_price);
    frm.set_value("total_selling_price_after_tax", total_selling_price_after_tax);

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
                let data = [];
                for (let item of r.message) {
                    let stock_info = await frappe.call({
                        method: "masar_mce.utils.get_current_stock_value_and_quantity",
                        args: { item_code: item.item_code },
                    });
                    let tax_info = await frappe.call({
                        method: "masar_mce.utils.get_tax_for_item",
                        args: { item_code: item.item_code },
                    });
                    let tax_rate = flt(tax_info.message) * 100;
                    let rate_after_tax = flt(item.rate) + flt(item.rate) * flt(tax_info.message);
                    let selling_after_tax =
                        flt(item.custom_selling_price) +
                        flt(item.custom_selling_price) * flt(tax_info.message);
                    data.push({
                        item_code: item.item_code,
                        item_name: item.item_name,
                        rate: item.rate || 0,
                        custom_selling_price: item.custom_selling_price || 0,
                        custom_markup_percentage: item.custom_markup_percentage || 0,
                        custom_purchase_price_after_tax: rate_after_tax,
                        custom_selling_price_after_tax: selling_after_tax,
                        current_stock_value: stock_info.message.value || 0,
                        current_quantity: stock_info.message.quantity || 0,
                        tax_rate: tax_rate
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
                                { fieldname: "rate", label: "Rate", fieldtype: "Currency", width: 100, in_list_view: 1 },
                                { fieldname: "custom_selling_price", label: "Selling Price", fieldtype: "Currency", width: 120, in_list_view: 1 },
                                { fieldname: "custom_markup_percentage", label: "Markup %", fieldtype: "Percent", width: 100, in_list_view: 1 },
                                { fieldname: "tax_rate", label: "Tax %", fieldtype: "Percent", width: 90, in_list_view: 1 },
                                { fieldname: "custom_purchase_price_after_tax", label: "Purchase Price After Tax", fieldtype: "Currency", width: 160, in_list_view: 1 },
                                { fieldname: "custom_selling_price_after_tax", label: "Selling Price After Tax", fieldtype: "Currency", width: 160, in_list_view: 1 },
                                { fieldname: "current_stock_value", label: "Current Stock Value", fieldtype: "Currency", width: 150, in_list_view: 1 },
                                { fieldname: "current_quantity", label: "Current Qty", fieldtype: "Float", width: 120, in_list_view: 1 }
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
                                new_row.rate = row.rate;
                                new_row.selling_price = row.custom_selling_price;
                                new_row.markup_percentage = row.custom_markup_percentage;
                                new_row.rate_after_tax = row.custom_purchase_price_after_tax;
                                new_row.selling_price_after_tax = row.custom_selling_price_after_tax;
                                new_row.current_stock_value = row.current_stock_value;
                                new_row.current_quantity = row.current_quantity;
                                new_row.tax_rate = row.tax_rate;
                            }
                        });
                        frm.refresh_field("items");
                        dialog.hide();
                    }
                });
                dialog.show();
            }
        });
    });
}
function GetLastSync(frm){
    frappe.call({
        doc: frm.doc,
        method: "get_last_sync",
        callback: function(r) {
            if(r.message) {
                frm.doc.last_sync = r.message;
                frm.refresh_field("last_sync");
            }
        }
    })
}
function CalculatePurchasePrice(frm, cdt, cdn){
    let row = locals[cdt][cdn];
    row.rate = flt(flt(row.current_stock_value) + flt(row.new_purchase_price) * flt(row.new_quantity)) / (flt(row.current_quantity) + flt(row.new_quantity));
    frm.refresh_field("items");
}