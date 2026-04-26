# Copyright (c) 2024, Leapp and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import validate_email_address


def _has_partner_role() -> bool:
    return "Leapp Partner" in frappe.get_roles(frappe.session.user)


@frappe.whitelist(allow_guest=False)
def resolve_instructor_by_email(email=None):
    """
    Resolve a single User by email for the partner offering instructor UI.
    Does not expose bulk user data. Caller must be a Leapp Partner.
    """
    if not _has_partner_role():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if not email or not isinstance(email, str):
        return {"ok": False, "message": _("Email is required.")}

    email = email.strip().lower()
    if not email:
        return {"ok": False, "message": _("Email is required.")}

    if not validate_email_address(email, throw=False):
        return {"ok": False, "message": _("Enter a valid email address.")}

    rows = frappe.get_all(
        "User",
        filters={"enabled": 1},
        or_filters=[["name", "=", email], ["email", "=", email]],
        fields=["name", "full_name", "email"],
        limit=1,
    )
    if not rows:
        return {"ok": False, "message": _("No account found for this email.")}

    user = rows[0]
    if "Leapp Partner" not in frappe.get_roles(user.name):
        return {
            "ok": False,
            "message": _("This email is not registered as a Leapp Partner."),
        }

    return {
        "ok": True,
        "name": user.name,
        "full_name": user.full_name or user.name,
        "email": user.email or email,
    }
