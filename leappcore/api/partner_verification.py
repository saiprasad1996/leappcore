# Copyright (c) 2026, Leapp and contributors
# For license information, please see license.txt

"""Whitelisted APIs for partner verification (partner submit + admin review)."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.utils.file_manager import save_file

from leappcore.backend.common.partner_verification import (
	apply_answers_from_form,
	get_latest_request,
	get_or_create_draft,
	send_verification_email,
	sync_profile_verification,
	validate_required_answers,
)


def _is_partner() -> bool:
	return "Leapp Partner" in frappe.get_roles(frappe.session.user)


def _is_admin() -> bool:
	roles = frappe.get_roles(frappe.session.user)
	return frappe.session.user == "Administrator" or "System Manager" in roles


def _parse_answers(answers) -> list:
	if answers is None:
		return []
	if isinstance(answers, str):
		try:
			answers = json.loads(answers)
		except Exception:
			frappe.throw(_("Invalid answers payload"))
	if not isinstance(answers, list):
		frappe.throw(_("Invalid answers payload"))
	return answers


@frappe.whitelist(allow_guest=False)
def save_draft(answers=None, request_name=None):
	"""Partner: save verification answers as Draft (or while Rejected / editing)."""
	if not _is_partner():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	user = frappe.session.user
	doc = get_or_create_draft(user)
	if doc.status == "Verified":
		frappe.throw(_("Your account is already verified."))
	if doc.status in ("Submitted", "Under Review"):
		frappe.throw(_("Your application is under review and cannot be edited."))

	# Rejected / Revoked path: if we got a fresh draft from revoked, status is Draft
	if doc.status == "Rejected":
		doc.status = "Draft"
		doc.rejection_reason = ""

	apply_answers_from_form(doc, _parse_answers(answers))
	_attach_uploaded_files(doc)
	doc.save(ignore_permissions=True)
	sync_profile_verification(user, "Draft", is_verified=0)
	frappe.db.commit()
	return {"ok": True, "name": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=False)
def submit_verification(answers=None):
	"""Partner: validate required fields and set Submitted."""
	if not _is_partner():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	user = frappe.session.user
	doc = get_or_create_draft(user)
	if doc.status == "Verified":
		frappe.throw(_("Your account is already verified."))
	if doc.status in ("Submitted", "Under Review"):
		frappe.throw(_("Your application is already submitted."))

	if doc.status in ("Rejected", "Revoked"):
		# Allow edit on Rejected; Revoked creates new draft in get_or_create_draft
		if doc.status == "Rejected":
			doc.rejection_reason = ""

	apply_answers_from_form(doc, _parse_answers(answers))
	_attach_uploaded_files(doc)
	validate_required_answers(doc)
	doc.status = "Submitted"
	doc.submitted_on = now_datetime()
	doc.reviewed_on = None
	doc.reviewed_by = None
	doc.save(ignore_permissions=True)
	sync_profile_verification(user, "Submitted", is_verified=0)
	frappe.db.commit()
	return {"ok": True, "name": doc.name, "status": doc.status}


def _attach_uploaded_files(doc) -> None:
	"""Pick up multipart files named answer__{field_key}."""
	if not frappe.request or not getattr(frappe.request, "files", None):
		return
	for row in doc.answers or []:
		if row.fieldtype != "Attach":
			continue
		key = f"answer__{row.field_key}"
		upload = frappe.request.files.get(key)
		if not upload or not getattr(upload, "filename", None):
			continue
		saved = save_file(
			upload.filename,
			upload.read(),
			"Partner Verification Request",
			doc.name,
			folder="Home/Attachments",
			is_private=1,
		)
		row.value_file = saved.file_url


@frappe.whitelist(allow_guest=False)
def admin_start_review(request_name: str):
	if not _is_admin():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = frappe.get_doc("Partner Verification Request", request_name)
	if doc.status != "Submitted":
		frappe.throw(_("Only Submitted applications can start review."))
	doc.status = "Under Review"
	doc.reviewed_by = frappe.session.user
	doc.save(ignore_permissions=True)
	sync_profile_verification(doc.partner, "Under Review", is_verified=0)
	frappe.db.commit()
	return {"ok": True, "status": doc.status}


@frappe.whitelist(allow_guest=False)
def admin_approve(request_name: str):
	if not _is_admin():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = frappe.get_doc("Partner Verification Request", request_name)
	if doc.status not in ("Submitted", "Under Review"):
		frappe.throw(_("Only Submitted or Under Review applications can be approved."))
	doc.status = "Verified"
	doc.reviewed_on = now_datetime()
	doc.reviewed_by = frappe.session.user
	doc.rejection_reason = ""
	doc.save(ignore_permissions=True)
	sync_profile_verification(doc.partner, "Verified", is_verified=1)
	frappe.db.commit()
	send_verification_email(doc.partner, "Verified")
	return {"ok": True, "status": doc.status}


@frappe.whitelist(allow_guest=False)
def admin_reject(request_name: str, reason: str = ""):
	if not _is_admin():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	reason = (reason or "").strip()
	if not reason:
		frappe.throw(_("Rejection reason is required."))
	doc = frappe.get_doc("Partner Verification Request", request_name)
	if doc.status not in ("Submitted", "Under Review"):
		frappe.throw(_("Only Submitted or Under Review applications can be rejected."))
	doc.status = "Rejected"
	doc.rejection_reason = reason
	doc.reviewed_on = now_datetime()
	doc.reviewed_by = frappe.session.user
	doc.save(ignore_permissions=True)
	sync_profile_verification(doc.partner, "Rejected", is_verified=0)
	frappe.db.commit()
	send_verification_email(doc.partner, "Rejected", reason)
	return {"ok": True, "status": doc.status}


@frappe.whitelist(allow_guest=False)
def admin_revoke(request_name: str):
	if not _is_admin():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = frappe.get_doc("Partner Verification Request", request_name)
	if doc.status != "Verified":
		frappe.throw(_("Only Verified partners can be revoked."))
	doc.status = "Revoked"
	doc.reviewed_on = now_datetime()
	doc.reviewed_by = frappe.session.user
	doc.save(ignore_permissions=True)
	sync_profile_verification(doc.partner, "Revoked", is_verified=0)
	frappe.db.commit()
	return {"ok": True, "status": doc.status}
