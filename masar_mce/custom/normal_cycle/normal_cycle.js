frappe.provide("masar_mce.buying_cycle");

masar_mce.buying_cycle.customizations = masar_mce.buying_cycle.customizations || {};

masar_mce.buying_cycle.is_normal = function (frm) {
    return cint(frm.doc.custom_normal_cycle) === 1;
};

masar_mce.buying_cycle.get_customizations = function (doctype) {
    const cache = masar_mce.buying_cycle.customizations;
    if (!cache[doctype]) {
        cache[doctype] = frappe
            .xcall("masar_mce.custom.normal_cycle.normal_cycle.get_cycle_customizations", { doctype })
            .catch(() => {
                delete cache[doctype];
                return { fields: [], doctype: [] };
            });
    }
    return cache[doctype];
};

masar_mce.buying_cycle.apply = async function (frm) {
    frappe.form.link_formatters["Item"] = masar_mce.buying_cycle.item_link_formatter;

    const data = await masar_mce.buying_cycle.get_customizations(frm.doctype);
    const normal = masar_mce.buying_cycle.is_normal(frm);
    const changed_tables = new Set();

    data.fields.forEach((d) => {
        if (d.property === "default") return;
        const value = normal ? d.standard : d.mce;
        if (d.table) {
            const grid = frm.fields_dict[d.table]?.grid;
            const df = grid && grid.docfields.find((df) => df.fieldname === d.fieldname);
            if (!df || df[d.property] === value) return;
            grid.update_docfield_property(d.fieldname, d.property, value);
            if (["in_list_view", "label"].includes(d.property)) changed_tables.add(d.table);
        } else if (frm.fields_dict[d.fieldname]) {
            frm.set_df_property(d.fieldname, d.property, value);
        }
    });

    data.doctype.forEach((d) => {
        frm.meta[d.property] = normal ? d.standard : d.mce;
    });

    changed_tables.forEach((table) => frm.fields_dict[table].grid.reset_grid());
    frm.refresh_fields();
    masar_mce.buying_cycle.apply_dashboard(frm, data.dashboard);
};
masar_mce.buying_cycle.apply_dashboard = function (frm, standard_dashboard) {
    const dashboard = frm.dashboard;
    const cycle = masar_mce.buying_cycle.is_normal(frm) ? "normal" : "mce";
    if (!dashboard || !standard_dashboard || dashboard.masar_cycle === cycle) return;
    if (!dashboard.masar_cycle && cycle === "mce") {
        dashboard.masar_cycle = cycle;
        return;
    }
    dashboard.masar_cycle = cycle;

    if (cycle === "normal") {
        dashboard.data = JSON.parse(JSON.stringify(standard_dashboard));
        dashboard.data.transactions = dashboard.data.transactions || [];
        dashboard.data.internal_links = dashboard.data.internal_links || {};
        dashboard.data.internal_and_external_links = dashboard.data.internal_and_external_links || {};
        dashboard.filter_permissions();
    } else {
        dashboard.data = null;
        dashboard.init_data();
    }

    dashboard.data_rendered = false;
    dashboard.transactions_area.empty();
    dashboard.refresh();
    dashboard.after_refresh();
};
masar_mce.buying_cycle.apply_defaults = async function (frm) {
    if (!frm.is_new()) return;
    const data = await masar_mce.buying_cycle.get_customizations(frm.doctype);
    const normal = masar_mce.buying_cycle.is_normal(frm);
    const evaluate = (df, value) =>
        value ? frappe.model.get_default_value({ ...df, default: value }, frm.doc) : "";

    data.fields.forEach((d) => {
        if (d.property !== "default" || d.table) return;
        const df = frappe.meta.get_docfield(frm.doctype, d.fieldname);
        if (!df) return;
        const from_value = evaluate(df, normal ? d.mce : d.standard);
        let to_value = evaluate(df, normal ? d.standard : d.mce) ?? "";
        if (to_value === "" && df.fieldtype === "Check") to_value = 0;
        if ((frm.doc[d.fieldname] ?? "") == (from_value ?? "")) {
            frm.set_value(d.fieldname, to_value);
        }
    });
};
masar_mce.buying_cycle.item_link_formatter = function (value, doc) {
    const parent = doc && doc.parenttype && locals[doc.parenttype] && locals[doc.parenttype][doc.parent];
    if (parent && cint(parent.custom_normal_cycle) === 1) {
        if (value && doc.item_name && doc.item_name !== value && doc.item_code === value) {
            return value + ": " + doc.item_name;
        } else if (!value && doc.doctype && doc.item_name) {
            return doc.item_name;
        }
        return value;
    }
    if (doc && doc.item_code && doc.item_name !== value) {
        return doc.item_code;
    }
    return value;
};
masar_mce.buying_cycle.set_item_query = function (frm, mce_query) {
    const field = frm.fields_dict.items.grid.get_field("item_code");
    if (!field.get_query || !field.get_query.is_mce_query) {
        field.standard_get_query = field.get_query;
    }
    if (masar_mce.buying_cycle.is_normal(frm)) {
        field.get_query = field.standard_get_query;
        return;
    }
    mce_query.is_mce_query = true;
    field.get_query = mce_query;
};

masar_mce.buying_cycle.standard_item_query = function (frm, args) {
    const field = frm.fields_dict.items.grid.get_field("item_code");
    return field.standard_get_query ? field.standard_get_query(...args) : {};
};

if (!masar_mce.buying_cycle.handlers_registered) {
    masar_mce.buying_cycle.handlers_registered = true;
    ["Purchase Order", "Purchase Receipt", "Purchase Invoice"].forEach((doctype) => {
        frappe.ui.form.on(doctype, {
            refresh(frm) {
                masar_mce.buying_cycle.apply(frm);
            },
            async custom_normal_cycle(frm) {
                await masar_mce.buying_cycle.apply_defaults(frm);
                frm.refresh();
            },
        });
    });
}
