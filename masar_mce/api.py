import frappe
from googletrans import Translator

@frappe.whitelist()
def translate_to_arabic(text):
    """Translate English text to Arabic using free Google Translate"""
    if not text:
        return ""

    try:
        translator = Translator()
        translated = translator.translate(text, src='en', dest='ar')
        return translated.text

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Translation Error")
        return "Translation failed"
