import frappe
import requests
import json


# from googletrans import Translator

# @frappe.whitelist()
# def translate_to_arabic(text):
#     """Translate English text to Arabic using free Google Translate"""
#     if not text:
#         return ""

#     try:
#         translator = Translator()
#         translated = translator.translate(text, src='en', dest='ar')
#         return translated.text

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Translation Error")
#         return "Translation failed"


def insert_pos_item(payload_local_zone, payload_free_zone):
    if payload_free_zone and payload_local_zone:
        headers = {
            "Content-Type": "application/json"
        }
        url = "http://192.168.70.70:85/api/agreement/insert"
        free_json = json.dumps(payload_free_zone, default=str)
        local_json = json.dumps(payload_local_zone, default=str)
        free_zone_response = requests.request("POST", url, headers=headers, data=free_json)
        local_zone_response = requests.request("POST", url, headers=headers, data=local_json)
        if free_zone_response.status_code in [200, 201, 202] and local_zone_response.status_code in [200, 201, 202]:
            frappe.msgprint("Item Successfully inserted", alert=True, indicator="green")
        else:
            frappe.throw(f"Error in inserting item:<br>Local Zone response: {local_zone_response.text}<br>Free Zone response: {free_zone_response.text}")


# def update_pos_item(payload_local_zone, payload_free_zone):
#     if payload_free_zone and payload_local_zone:
#         headers = {
#             "Content-Type": "application/json"
#         }
#         url = "http://192.168.70.70:85/api/agreement/insert"
#         free_zone_response = requests.request("POST", url, headers=headers, data=json.dumps(payload_free_zone))
#         local_zone_response = requests.request("POST", url, headers=headers, data=json.dumps(payload_local_zone))
#         if free_zone_response.status_code in [200, 201, 202] and local_zone_response.status_code in [200, 201, 202]:
#             frappe.msgprint("Item Successfuly updated", alert=True, indicator="green")
#         else:
#             frappe.throw(f"Error in inserting item:<br>Local Zone response: {local_zone_response.text}<br>Free Zone response: {free_zone_response.text}")

        # url = "http://192.168.70.70:85/api/agreement/update-item"
        # free_zone_response = requests.request("PUT", url, headers=headers, data=json.dumps(payload_free_zone))
        # local_zone_response = requests.request("PUT", url, headers=headers, data=json.dumps(payload_local_zone))
        # if free_zone_response.status_code in [200, 201, 202] and local_zone_response.status_code in [200, 201, 202]:
        #     frappe.msgprint("Item Successfuly Updated", alert=True, indicator="green")
        # else:
        #     frappe.throw(f"Error in updating item:<br>Local Zone response: {local_zone_response.text}<br>Free Zone response: {free_zone_response.text}")