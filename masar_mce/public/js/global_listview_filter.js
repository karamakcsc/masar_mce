const OriginalListView = frappe.views.ListView;

frappe.views.ListView = class CustomListView extends OriginalListView {
    before_render() {
        super.before_render();

        const filters = this.filter_area?.get() || [];

        const has_docstatus_filter = filters.some(
            f => f[1] === "docstatus"
        );

        if (!has_docstatus_filter) {
            this.filter_area.add([
                [this.doctype, "docstatus", "=", 0]
            ]);
        }
    }
};