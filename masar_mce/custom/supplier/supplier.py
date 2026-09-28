import frappe

def autoname(self, method):
#     # Runs after ERPNext's Supplier.autoname: replace the series name with max numeric code + 1
    # self.custom_supplier_code = str(get_next_supplier_code())
    self.name = self.custom_supplier_code

# def get_next_supplier_code():
#     # Check both name and code: they can drift apart if the code is edited later
#     max_code = frappe.db.sql("""
#         SELECT GREATEST(
#             COALESCE(MAX(CASE WHEN custom_supplier_code REGEXP '^[0-9]+$' THEN CAST(custom_supplier_code AS UNSIGNED) END), 0),
#             COALESCE(MAX(CASE WHEN name REGEXP '^[0-9]+$' THEN CAST(name AS UNSIGNED) END), 0)
#         )
#         FROM `tabSupplier`
#         FOR UPDATE
#     """)[0][0]
#     return int(max_code or 0) + 1

# def after_insert(self, method):
#     self.custom_supplier_code = self.name
#     frappe.db.set_value("Supplier", self.name, "custom_supplier_code", self.custom_supplier_code , update_modified=False)