import json

import frappe


def execute():
	settings = frappe.get_single("API Settings")
	if settings.url:
		return

	settings.enabled = 1
	settings.url = "http://192.168.70.70:85/api/agreement/insert"
	settings.request_method = "POST"
	settings.timeout = 30
	settings.headers = json.dumps({"Content-Type": "application/json"}, indent=4)
	settings.save(ignore_permissions=True)
