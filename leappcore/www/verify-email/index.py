import frappe
from frappe import _

from leappcore.signup_notifications import VERIFY_EMAIL_CACHE_PREFIX


def get_context(context):
    context.no_cache = 1
    token = (frappe.request.args.get("token") or "").strip()
    if not token or len(token) > 64:
        context.verify_status = "invalid"
        context.page_title = _("Invalid link")
        return context

    cache_key = f"{VERIFY_EMAIL_CACHE_PREFIX}{token}"
    email = frappe.cache.get_value(cache_key)
    if not email:
        context.verify_status = "expired"
        context.page_title = _("Link expired")
        return context

    if not frappe.db.exists("User", email):
        frappe.cache.delete_value(cache_key)
        context.verify_status = "invalid"
        context.page_title = _("Invalid link")
        return context

    frappe.cache.delete_value(cache_key)

    context.verify_status = "ok"
    context.page_title = _("Email verified")
    return context
