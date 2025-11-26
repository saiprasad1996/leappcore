import frappe


def get_context(context):
    context.no_cache = 1
    context.message = frappe.form_dict.get("message")
