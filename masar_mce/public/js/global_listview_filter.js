// public/js/listview_default_filter.js

// frappe.listview_settings is looked up per-doctype
// (frappe.listview_settings[this.doctype] in base_list.js), so a literal
// "*" key is never read and its onload never fires for any doctype.
// Instead we wrap frappe.listview_settings in a Proxy so that looking up
// ANY doctype's settings returns a real onload — chained after that
// doctype's own onload, if one is defined.
frappe.provide("frappe.listview_settings");

const original_listview_settings = frappe.listview_settings;

frappe.listview_settings = new Proxy(original_listview_settings, {
    get(target, prop, receiver) {
        // Let symbols and inherited Object methods (hasOwnProperty, toString, ...)
        // pass through untouched — they are not doctype names.
        if (typeof prop === "symbol" || prop in Object.prototype) {
            return Reflect.get(target, prop, receiver);
        }

        const doctype_settings = target[prop] || {};
        const original_onload = doctype_settings.onload;

        return Object.assign({}, doctype_settings, {
            onload(listview) {
                original_onload && original_onload.call(this, listview);
                apply_default_docstatus_filter(listview);
            },
        });
    },
    set(target, prop, value) {
        target[prop] = value;
        return true;
    },
});

function apply_default_docstatus_filter(listview) {
    // Prevent re-application if already processed in this listview instance
    if (listview.__default_filter_applied) {
        return;
    }

    // Mark as applied immediately to avoid duplicate calls (even if the filter fails)
    listview.__default_filter_applied = true;

    // Get current filters (array of arrays: [doctype, field, operator, value])
    const current_filters = listview.filter_area.get() || [];

    // Check if a docstatus filter already exists (from saved filters or default)
    const has_docstatus_filter = current_filters.some(
        (f) => f[1] === "docstatus"  // field name is the second element
    );

    // Only add our default if no docstatus filter is present
    if (!has_docstatus_filter) {
        // filter_area.add() already triggers a list refresh by default;
        // FilterArea has no separate apply() method.
        listview.filter_area.add([
            [listview.doctype, "docstatus", "=", 0]
        ]);
    }
}
