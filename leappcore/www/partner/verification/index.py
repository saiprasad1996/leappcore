import frappe
from frappe import _

from leappcore.backend.common.partner_verification import (
	get_active_template,
	get_latest_request,
	get_or_create_draft,
	get_partner_type,
	is_partner_verified,
)


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/partner/verification"
		raise frappe.Redirect

	if "Leapp Partner" not in frappe.get_roles(frappe.session.user):
		frappe.local.flags.redirect_location = "/courses"
		raise frappe.Redirect

	context.csrf_token = frappe.sessions.get_csrf_token()
	context.no_cache = 1
	user = frappe.session.user

	context.partner_type = get_partner_type(user)
	context.is_verified = is_partner_verified(user)
	# Do not use context.template — Frappe website renderer expects that for the Jinja path
	context.verification_template = None
	context.request_doc = None
	context.field_rows = []
	context.status = "Not Started"
	context.rejection_reason = ""
	context.can_edit = False
	context.error_message = None

	verification_template = get_active_template(context.partner_type)
	context.verification_template = verification_template

	if not verification_template:
		context.error_message = _(
			"No verification checklist is configured for {0} partners yet. Please check back later."
		).format(context.partner_type)
		return context

	latest = get_latest_request(user)
	if latest and latest.status == "Verified":
		context.request_doc = latest
		context.status = latest.status
		context.field_rows = _serialize_answers(latest)
		context.can_edit = False
		return context

	# Ensure draft exists for editable states
	try:
		if not latest or latest.status in ("Draft", "Rejected", "Revoked", None):
			doc = get_or_create_draft(user)
		else:
			doc = latest
	except Exception as e:
		context.error_message = str(e)
		return context

	context.request_doc = doc
	context.status = doc.status
	context.rejection_reason = doc.rejection_reason or ""
	context.can_edit = doc.status in ("Draft", "Rejected")
	context.field_rows = _serialize_answers(doc)
	# help text from template
	help_by_key = {r.field_key: r.description for r in (verification_template.fields or [])}
	req_by_key = {r.field_key: bool(r.reqd) for r in (verification_template.fields or [])}
	for row in context.field_rows:
		row["description"] = help_by_key.get(row["field_key"]) or ""
		row["reqd"] = req_by_key.get(row["field_key"], False)

	return context


def _serialize_answers(doc):
	rows = []
	for row in doc.answers or []:
		value = ""
		if row.fieldtype in ("Text", "Long Text"):
			value = row.value_text or ""
		elif row.fieldtype in ("Int", "Decimal"):
			value = "" if row.value_number is None else row.value_number
		elif row.fieldtype == "Check":
			value = 1 if row.value_check else 0
		elif row.fieldtype == "Attach":
			value = row.value_file or ""
		rows.append(
			{
				"field_key": row.field_key,
				"label": row.label,
				"fieldtype": row.fieldtype,
				"value": value,
			}
		)
	return rows
