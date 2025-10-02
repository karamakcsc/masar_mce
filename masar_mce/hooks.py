app_name = "masar_mce"
app_title = "Masar MCE"
app_publisher = "KCSC"
app_description = "Masar MCE"
app_email = "info@kcsc.com.jo"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "masar_mce",
# 		"logo": "/assets/masar_mce/logo.png",
# 		"title": "Masar MCE",
# 		"route": "/masar_mce",
# 		"has_permission": "masar_mce.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/masar_mce/css/masar_mce.css"
# app_include_js = "/assets/masar_mce/js/masar_mce.js"

# include js, css files in header of web template
# web_include_css = "/assets/masar_mce/css/masar_mce.css"
# web_include_js = "/assets/masar_mce/js/masar_mce.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "masar_mce/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Blanket Order" : "custom/blanket_order/blanket_order.js", 
    "Stock Entry" : "custom/stock_entry/stock_entry.js", 
    "Purchase Order" : "custom/purchase_order/purchase_order.js"
    }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "masar_mce/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "masar_mce.utils.jinja_methods",
# 	"filters": "masar_mce.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "masar_mce.install.before_install"
# after_install = "masar_mce.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "masar_mce.uninstall.before_uninstall"
# after_uninstall = "masar_mce.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "masar_mce.utils.before_app_install"
# after_app_install = "masar_mce.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "masar_mce.utils.before_app_uninstall"
# after_app_uninstall = "masar_mce.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "masar_mce.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Item": {
        "after_insert": "masar_mce.custom.Item.item.after_insert",
        "on_update": "masar_mce.custom.Item.item.on_update",
    }, 
    "Quality Inspection": {
        "on_submit": "masar_mce.custom.quality_inspection.quality_inspection.on_submit"
    }, 
    "Stock Entry":{
        "on_submit": "masar_mce.custom.stock_entry.stock_entry.on_submit"
    }, 
    "Blanket Order" : {
        "validate" : "masar_mce.custom.blanket_order.blanket_order.validate"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"masar_mce.tasks.all"
# 	],
# 	"daily": [
# 		"masar_mce.tasks.daily"
# 	],
# 	"hourly": [
# 		"masar_mce.tasks.hourly"
# 	],
# 	"weekly": [
# 		"masar_mce.tasks.weekly"
# 	],
# 	"monthly": [
# 		"masar_mce.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "masar_mce.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "masar_mce.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "masar_mce.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["masar_mce.utils.before_request"]
# after_request = ["masar_mce.utils.after_request"]

# Job Events
# ----------
# before_job = ["masar_mce.utils.before_job"]
# after_job = ["masar_mce.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"masar_mce.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
fixtures = [
    {"dt": "Custom Field", "filters": [
        [
            "name", "in", [
                'Blanket Order-custom_column_break_bqf6r',
                'Blanket Order-custom_total_quantity',
                'Blanket Order-custom_section_break_a5ugk',
                'Purchase Order Item-custom_blanket_order_item',
                'Blanket Order-custom_special_terms',
                'Blanket Order-custom_tcs_terms',
                'Blanket Order-custom_special_terms_tab',
                'Blanket Order-custom_general_terms',
                'Blanket Order-custom_total',
                'Stock Entry Detail-custom_quality_inspection_status',
                'Blanket Order Item-custom_quality_inspection_remarks',
                'Blanket Order Item-custom_quality_inspection_status',
                'Blanket Order Item-custom_column_break_ijewz',
                'Blanket Order Item-custom_quality_inspection',
                'Blanket Order Item-custom_amount',
                'Blanket Order Item-custom_section_break_uoh6p',
                'Blanket Order Item-custom_selling_price',
                'Purchase Order-custom_supplier_agreement',
                'Blanket Order Item-custom_markup_percentage',
                'Blanket Order-custom_pricing_type',
                'Terms and Conditions-custom_special_terms',
                'Stock Entry-custom_supplier_agreement',
                'Purchase Order-custom_get_all_items',
                'Blanket Order-custom_penalties',
                'Blanket Order-custom_penalties_tab'
            ]
        ]
    ]},
    {"dt": "Translation", "filters": [
        [
            "name", "in", [
                "eu7jh96i2v"
            ]
        ]
    ]
    },
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "name",
                "in",
                [
                   'Supplier-naming_series-hidden',
                    'Supplier-naming_series-reqd',
                    'Purchase Order Item-main-field_order',
                    'Stock Entry-main-field_order',
                    'Blanket Order Item-main-field_order',
                    'Blanket Order-tc_name-link_filters',
                    'Terms and Conditions-main-field_order',
                    'Blanket Order-main-field_order',
                    'Blanket Order Item-rate-label',
                    'Stock Entry Detail-main-field_order',
                    'Blanket Order-blanket_order_type-read_only',
                    'Blanket Order-blanket_order_type-default',
                    'Purchase Order-main-field_order', 
                    'Blanket Order-main-protect_attached_files' , 
                    'Blanket Order-blanket_order_type-hidden' , 
                    'Blanket Order-order_no-hidden'
                ]
            ]
                ]
    }
]
