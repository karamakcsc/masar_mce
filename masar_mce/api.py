import frappe
import requests
import json


def get_api_settings():
    settings = frappe.get_single("API Settings")
    if not settings.enabled:
        frappe.throw("API Settings is disabled. Enable it before making this request.")
    headers = json.loads(settings.headers) if settings.headers else {}
    return settings.url, headers, settings.request_method, settings.timeout


def insert_pos_item(payload_local_zone, payload_free_zone):
    if payload_free_zone and payload_local_zone:
        url, headers, method, timeout = get_api_settings()
        free_json = json.dumps(payload_free_zone, default=str)
        local_json = json.dumps(payload_local_zone, default=str)
        free_zone_response = requests.request(method, url, headers=headers, data=free_json, timeout=timeout)
        local_zone_response = requests.request(method, url, headers=headers, data=local_json, timeout=timeout)
        if free_zone_response.status_code in [200, 201, 202] and local_zone_response.status_code in [200, 201, 202]:
            frappe.msgprint("Item Successfully inserted", alert=True, indicator="green")
        else:
            frappe.throw(f"Error in inserting item:<br>Local Zone response: {local_zone_response.text}<br>Free Zone response: {free_zone_response.text}")