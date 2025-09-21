// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt
frappe.ui.form.on("Penalty", {
    refresh: function(frm) {
        set_autocompletions_for_condition_formula(frm);
    },
    onload: function(frm) {
        set_autocompletions_for_condition_formula(frm);
    }
});

function set_autocompletions_for_condition_formula(frm) {
    const autocompletions = [];
    const doctypes = [
        "Purchase Receipt",
        "Purchase Order",
        "Purchase Invoice",
        "Blanket Order"
    ];

    frappe.run_serially([
        () => {
            return Promise.all(
                doctypes.map(doctype => 
                    frappe.model.with_doctype(doctype, () => {
                        const fields = frappe.get_meta(doctype).fields;
                        let metaLabel = `${doctype} Field`;
                        if (doctype === "Blanket Order") {
                            metaLabel = "Supplier Agreement Field";
                        }
                        autocompletions.push(
                            ...fields.map(f => ({
                                value: f.fieldname,
                                score: 10,
                                meta: metaLabel,
                            }))
                        );
                    })
                )
            );
        },
        () => {
            frm.set_df_property("penalty_formula", "autocompletions", autocompletions);
            frm.refresh_field("penalty_formula");
        }
    ]);
}