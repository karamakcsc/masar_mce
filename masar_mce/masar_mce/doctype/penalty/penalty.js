frappe.ui.form.on("Penalty", {
    refresh: function(frm) {
        set_autocompletions_for_condition_formula(frm);
    },
    onload: function(frm) {
        set_autocompletions_for_condition_formula(frm);
    },
    penalty_formula: function(frm) {
        set_formula_doctype_from_autocompletions(frm);
    },
    formula_doctype: function(frm) {
        set_autocompletions_for_condition_formula(frm);
    }
});

function set_autocompletions_for_condition_formula(frm) {
    const autocompletions = [];
    const formula_doctype = frm.doc.formula_doctype;
    const doctypes = formula_doctype ? [formula_doctype] : ["Purchase Receipt", "Blanket Order"];

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
            frm.autocompletions = autocompletions;
        }
    ]);
}

function set_formula_doctype_from_autocompletions(frm) {
    if (!frm.doc.penalty_formula || !frm.autocompletions) {
        frm.set_value('formula_doctype', null);
    frm.refresh_field("formula_doctype");
    }
    
    const formula = frm.doc.penalty_formula.toLowerCase();
    let detectedDoctype = null;
    frm.autocompletions.forEach(item => {
        if (formula.includes(item.value.toLowerCase())) {
            if (item.meta === "Purchase Receipt Field") {
                detectedDoctype = "Purchase Receipt";
            } else if (item.meta === "Supplier Agreement Field") {
                detectedDoctype = "Blanket Order";
            }
        }
    });
    frm.set_value('formula_doctype', detectedDoctype);
    frm.refresh_field("formula_doctype");

}
