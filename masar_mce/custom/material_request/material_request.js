frappe.ui.form.on("Material Request", {
    setup(frm) {
        defaultSection(frm);
    }, 
    refresh(frm) {
        defaultSection(frm);
    }, 
    onload(frm) {
        defaultSection(frm);
    },
    before_workflow_action: function(frm) {
        if (frm.selected_workflow_action === 'Approve') {
            return new Promise((resolve, reject) => {
                frappe.db.get_doc('Warehouse', frm.doc.set_from_warehouse)
                    .then(warehouse => {
                        let is_authorized = warehouse.custom_users.some(row => row.user === frappe.session.user);
                        if (is_authorized) {
                            resolve(); 
                        } else {
                            frappe.msgprint(__('You are not authorized to approve for Warehouse: {0}', [frm.doc.set_from_warehouse]));
                            reject(); 
                        }
                    })
                    .catch(err => {
                        frappe.msgprint(__('Error verifying warehouse permissions.'));
                        reject();
                    });
            });
        }
    }
});

function defaultSection(frm){
     setTimeout(() => {    
            cur_frm.page.remove_inner_button(__('Sales Order'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Bill of Materials'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Product Bundle'),  __('Get Items From'));
            cur_frm.page.remove_inner_button(__('Pick List'),  __('Create'));
        },100);
}