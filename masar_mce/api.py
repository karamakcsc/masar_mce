import frappe
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
    """Wait for the API from MCE"""
    pass

def update_pos_item(payload_local_zone, payload_free_zone):
    """Wait for the API from MCE"""
    pass