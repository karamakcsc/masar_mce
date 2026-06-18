frappe.ui.form.on("Material Request", {
    setup(frm) {
        defaultSection(frm);
        const grid = frm.fields_dict["items"].grid;
        const tWarehouseField = grid.get_field("from_warehouse");
        if (!tWarehouseField.original_bonus_get_query) {
            tWarehouseField.original_bonus_get_query =
                tWarehouseField.get_query;
        }
        tWarehouseField.get_query = function () {
            return {
                filters: {
                    warehouse_type: ["in", ["مركزي"]]
                }
            };
        };
        frm.set_query("set_from_warehouse", function () {
        return {
            filters: {
                warehouse_type: ["in", ["مركزي"]]
            }
        };
    });
    }, 
    refresh(frm) {
                const grid = frm.fields_dict["items"].grid;
        const tWarehouseField = grid.get_field("from_warehouse");
        if (!tWarehouseField.original_bonus_get_query) {
            tWarehouseField.original_bonus_get_query =
                tWarehouseField.get_query;
        }
        tWarehouseField.get_query = function () {
            return {
                filters: {
                    warehouse_type: ["in", ["مركزي"]]
                }
            };
        };
        frm.set_query("set_from_warehouse", function () {
        return {
            filters: {
                warehouse_type: ["in", ["مركزي"]]
            }
        };
    });
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