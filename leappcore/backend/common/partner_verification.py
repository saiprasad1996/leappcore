# Copyright (c) 2026, Leapp and contributors
# For license information, please see license.txt

"""Shared helpers for partner verification status and badge."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


ACTIVE_REQUEST_STATUSES = ("Draft", "Submitted", "Under Review", "Rejected")
TERMINAL_OK = "Verified"


def is_partner_verified(user: str | None) -> bool:
	"""Return True if Partner Profile is verified for badge display."""
	if not user:
		return False
	return bool(
		frappe.db.get_value("Partner Profile", {"user": user}, "is_verified")
		or frappe.db.get_value("Partner Profile", user, "is_verified")
	)


def get_partner_profile_name(user: str) -> str | None:
	"""Resolve Partner Profile name for a User (autoname is format:{user})."""
	if not user:
		return None
	if frappe.db.exists("Partner Profile", user):
		return user
	name = frappe.db.get_value("Partner Profile", {"user": user}, "name")
	return name


def get_partner_type(user: str) -> str:
	"""Return Individual/Organisation; default Individual for legacy profiles."""
	profile_name = get_partner_profile_name(user)
	if not profile_name:
		return "Individual"
	ptype = frappe.db.get_value("Partner Profile", profile_name, "partner_type")
	return ptype or "Individual"


def sync_profile_verification(user: str, status: str, is_verified: int | None = None) -> None:
	"""Update denormalized Partner Profile verification fields."""
	profile_name = get_partner_profile_name(user)
	if not profile_name:
		return
	values = {"verification_status": status}
	if is_verified is not None:
		values["is_verified"] = 1 if is_verified else 0
	else:
		values["is_verified"] = 1 if status == "Verified" else 0
	frappe.db.set_value("Partner Profile", profile_name, values, update_modified=False)


def get_active_template(partner_type: str):
	"""Return active Partner Verification Template for type, or None."""
	name = frappe.db.get_value(
		"Partner Verification Template",
		{"partner_type": partner_type, "is_active": 1},
		"name",
	)
	if not name:
		# fallback: any template for type
		name = frappe.db.get_value(
			"Partner Verification Template",
			{"partner_type": partner_type},
			"name",
		)
	if not name:
		return None
	return frappe.get_doc("Partner Verification Template", name)


def get_latest_request(user: str):
	"""Latest verification request for partner (any status)."""
	name = frappe.db.get_value(
		"Partner Verification Request",
		{"partner": user},
		"name",
		order_by="creation desc",
	)
	if not name:
		return None
	return frappe.get_doc("Partner Verification Request", name)


def get_or_create_draft(user: str):
	"""
	Return an editable request (Draft or Rejected ready for edit), or create Draft.
	Verified partners get no new draft until Revoked.
	"""
	latest = get_latest_request(user)
	if latest:
		if latest.status == "Verified":
			return latest
		if latest.status in ("Draft", "Rejected", "Revoked"):
			if latest.status == "Revoked":
				# Start fresh draft after revoke
				return _create_draft(user)
			return latest
		# Submitted / Under Review — return as-is (read-only for partner)
		return latest

	return _create_draft(user)


def _create_draft(user: str):
	partner_type = get_partner_type(user)
	template = get_active_template(partner_type)
	if not template:
		frappe.throw(
			_("No verification checklist is configured for {0} partners. Please contact support.").format(
				partner_type
			)
		)

	doc = frappe.get_doc(
		{
			"doctype": "Partner Verification Request",
			"partner": user,
			"partner_type": partner_type,
			"template": template.name,
			"status": "Draft",
			"answers": [
				{
					"field_key": row.field_key,
					"label": row.label,
					"fieldtype": row.fieldtype,
				}
				for row in (template.fields or [])
			],
		}
	)
	doc.insert(ignore_permissions=True)
	sync_profile_verification(user, "Draft", is_verified=0)
	return doc


def apply_answers_from_form(doc, answers: list[dict], files: dict | None = None) -> None:
	"""Merge submitted answer payloads into request child rows."""
	files = files or {}
	by_key = {row.field_key: row for row in (doc.answers or [])}
	for item in answers or []:
		if not isinstance(item, dict):
			continue
		key = item.get("field_key")
		if not key or key not in by_key:
			continue
		row = by_key[key]
		ft = row.fieldtype
		if ft in ("Text", "Long Text"):
			row.value_text = item.get("value") or ""
		elif ft in ("Int", "Decimal"):
			raw = item.get("value")
			row.value_number = float(raw) if raw not in (None, "") else None
		elif ft == "Check":
			row.value_check = 1 if item.get("value") in (1, "1", True, "true", "on") else 0
		elif ft == "Attach":
			# File saved separately; allow URL pass-through
			if item.get("value"):
				row.value_file = item.get("value")


def validate_required_answers(doc) -> None:
	missing = []
	template = frappe.get_doc("Partner Verification Template", doc.template)
	req_keys = {r.field_key for r in (template.fields or []) if r.reqd}
	for row in doc.answers or []:
		if row.field_key not in req_keys:
			continue
		ok = False
		if row.fieldtype in ("Text", "Long Text"):
			ok = bool((row.value_text or "").strip())
		elif row.fieldtype in ("Int", "Decimal"):
			ok = row.value_number is not None
		elif row.fieldtype == "Check":
			ok = True  # unchecked is a valid boolean
		elif row.fieldtype == "Attach":
			ok = bool(row.value_file)
		if not ok:
			missing.append(row.label or row.field_key)
	if missing:
		frappe.throw(_("Please complete required fields: {0}").format(", ".join(missing)))


def send_verification_email(user: str, status: str, rejection_reason: str = "") -> None:
	"""Email partner on Verified or Rejected."""
	if status not in ("Verified", "Rejected"):
		return
	email = frappe.db.get_value("User", user, "email") or user
	full_name = frappe.db.get_value("User", user, "full_name") or email
	if status == "Verified":
		subject = _("Your LEAPP partner account is verified")
		body = f"""
		<p>Hi {frappe.utils.escape_html(full_name)},</p>
		<p>Congratulations — your LEAPP partner verification has been approved.
		A verified badge will now appear next to your name on the platform.</p>
		<p><a href="{frappe.utils.get_url('/partner/verification')}">View verification status</a></p>
		"""
	else:
		reason = rejection_reason or _("No reason provided.")
		subject = _("Your LEAPP partner verification needs updates")
		body = f"""
		<p>Hi {frappe.utils.escape_html(full_name)},</p>
		<p>Your partner verification was not approved. Please review the feedback,
		update your details, and resubmit.</p>
		<p><strong>Reason:</strong></p>
		<p>{frappe.utils.escape_html(reason)}</p>
		<p><a href="{frappe.utils.get_url('/partner/verification')}">Update and resubmit</a></p>
		"""
	try:
		frappe.sendmail(
			recipients=[email],
			subject=subject,
			message=body,
			delayed=False,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Partner Verification Email Error")
