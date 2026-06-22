frappe.listview_settings['Stock Entry'] = {
    refresh: function(listview) {
        if (frappe.session.user !== 'Administrator'
            && frappe.user_roles.includes('مسؤول لجنة الاستلام')) {
            listview.page.clear_primary_action();
        }
    }
};