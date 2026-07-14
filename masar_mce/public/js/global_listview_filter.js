// public/js/listview_default_filter.js

frappe.listview_settings["*"] = {
    onload(listview) {
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
            listview.filter_area.add([
                [listview.doctype, "docstatus", "=", 0]
            ]);
            // After adding, we must refresh the list to apply the filter
            listview.filter_area.apply();
        }
    }
};