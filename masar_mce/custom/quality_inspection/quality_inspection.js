frappe.ui.form.on('Quality Inspection', {
    refresh: function(frm) {
        if (
            frm.doc.docstatus === 1 &&
            frm.doc.status === "Rejected" &&
            frm.doc.reference_type === "Stock Entry"
        ) {
            frm.add_custom_button(__('Penalty Entry'), function() {

                frappe.model.open_mapped_doc({
                    method: "masar_mce.custom.quality_inspection.quality_inspection.make_penalty_entry",
                    frm: frm
                });

            }, __('Create'));
        }
    }
});