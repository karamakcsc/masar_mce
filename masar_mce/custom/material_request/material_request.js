frappe.ui.form.on("Material Request", {
    setup(frm) {
        defaultSection(frm);
    }, 
    refresh(frm) {
        defaultSection(frm);
    }, 
    onload(frm) {
        defaultSection(frm);
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