########################## Siam 18-06-2026
import frappe

user_role = {
    "مدير السوق",
    "موظف السوق",
    "مسؤول لجنة الاستلام",
}
except_roles = {"System Manager", "Purchase Manager", "Purchase User"}


def get_permission_query_conditions(user=None):
    if not user:
        user = frappe.session.user

    # المدير الأعلى لا يُقيَّد
    if user == "Administrator":
        return ""

    roles = set(frappe.get_roles(user))

    # طبّق القيد فقط على عضو اللجنة الذي لا يحمل دوراً أعلى
    if (roles & user_role) and not (roles & except_roles):
        return "`tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.custom_is_wh_only = 0"

    return ""