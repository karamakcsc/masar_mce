import json
import functools
import frappe

NORMAL_CYCLE_FIELD = "custom_normal_cycle"

FORM_PROPERTIES = {
    "hidden": 0,
    "read_only": 0,
    "reqd": 0,
    "label": "",
    "description": "",
    "depends_on": "",
    "read_only_depends_on": "",
    "mandatory_depends_on": "",
    "collapsible": 0,
    "default": "",
}
CHILD_ONLY_PROPERTIES = {"in_list_view": 0}
DOCTYPE_PROPERTIES = {"default_print_format": ""}
LAYOUT_FIELDTYPES = ("Section Break", "Column Break", "Tab Break")


def is_normal_cycle(doc):
    return bool(doc and doc.get(NORMAL_CYCLE_FIELD))


def skip_if_normal_cycle(fn):
    @functools.wraps(fn)
    def wrapper(doc, *args, **kwargs):
        if is_normal_cycle(doc):
            return
        return fn(doc, *args, **kwargs)
    return wrapper


def get_standard_doctype_json(doctype):
    module = frappe.db.get_value("DocType", doctype, "module")
    scrubbed = frappe.scrub(doctype)
    path = frappe.get_module_path(module, "doctype", scrubbed, scrubbed + ".json")
    with open(path) as f:
        return json.load(f)


@frappe.whitelist()
def get_cycle_customizations(doctype):
    if doctype not in ("Purchase Order", "Purchase Receipt", "Purchase Invoice"):
        frappe.throw(frappe._("Normal Cycle is not supported for {0}").format(doctype))
    frappe.has_permission(doctype, throw=True)

    tables = {None: doctype}
    for df in frappe.get_meta(doctype).get_table_fields():
        tables[df.fieldname] = df.options

    fields = []
    for table_field, dt in tables.items():
        standard_fields = {d.get("fieldname"): d for d in get_standard_doctype_json(dt).get("fields", [])}
        allowed = dict(FORM_PROPERTIES, **(CHILD_ONLY_PROPERTIES if table_field else {}))

        for ps in frappe.get_all(
            "Property Setter",
            filters={"doc_type": dt, "doctype_or_field": "DocField", "property": ["in", list(allowed)]},
            fields=["field_name", "property", "property_type", "value"],
        ):
            std = standard_fields.get(ps.field_name)
            if not std or ps.field_name == "naming_series":
                continue
            mce_value = cast_value(ps.value, ps.property_type)
            standard_value = std.get(ps.property, allowed[ps.property])
            if mce_value == standard_value:
                continue
            fields.append({
                "table": table_field,
                "fieldname": ps.field_name,
                "property": ps.property,
                "mce": mce_value,
                "standard": standard_value,
            })

        for cf in frappe.get_all(
            "Custom Field",
            filters={"dt": dt, "fieldtype": ["not in", LAYOUT_FIELDTYPES]},
            fields=["fieldname", "hidden", "reqd", "mandatory_depends_on"],
        ):
            if not cf.fieldname.startswith("custom_") or cf.fieldname == NORMAL_CYCLE_FIELD:
                continue
            for prop, standard in (("hidden", 1), ("reqd", 0), ("mandatory_depends_on", "")):
                mce_value = cf[prop] or type(standard)()
                if mce_value != standard:
                    fields.append({
                        "table": table_field,
                        "fieldname": cf.fieldname,
                        "property": prop,
                        "mce": mce_value,
                        "standard": standard,
                    })

    standard_doctype = get_standard_doctype_json(doctype)
    doctype_properties = []
    for ps in frappe.get_all(
        "Property Setter",
        filters={"doc_type": doctype, "doctype_or_field": "DocType", "property": ["in", list(DOCTYPE_PROPERTIES)]},
        fields=["property", "value"],
    ):
        doctype_properties.append({
            "property": ps.property,
            "mce": ps.value,
            "standard": standard_doctype.get(ps.property) or DOCTYPE_PROPERTIES[ps.property],
        })

    return {"fields": fields, "doctype": doctype_properties, "dashboard": get_standard_dashboard(doctype)}


def get_standard_dashboard(doctype):
    """Dashboard (connections) data of the doctype without the MCE `override_doctype_dashboards` hooks."""
    from frappe.modules import load_doctype_module

    meta = frappe.get_meta(doctype)
    data = frappe._dict()
    try:
        module = load_doctype_module(doctype, suffix="_dashboard")
        if hasattr(module, "get_data"):
            data = frappe._dict(module.get_data())
    except ImportError:
        pass
    meta.add_doctype_links(data)
    return data


def cast_value(value, property_type):
    if property_type in ("Check", "Int"):
        return frappe.utils.cint(value)
    return value or ""
