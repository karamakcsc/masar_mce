def custom_stock_entry_dashboard(data=None):
    return {
        "fieldname": "reference_name",
        "non_standard_fieldnames": {
            "Quality Inspection": "reference_name"
        },
        "internal_links": {},
        "transactions": [
            {
                "label": "Reference",
                "items": ["Quality Inspection"]
            }
        ]
    }