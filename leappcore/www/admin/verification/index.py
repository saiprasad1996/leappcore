import frappe
from frappe import _
from frappe.utils import format_datetime


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/admin/verification"
		raise frappe.Redirect

	user_roles = frappe.get_roles(frappe.session.user)
	if frappe.session.user != "Administrator" and "System Manager" not in user_roles:
		frappe.local.flags.redirect_location = "/"
		raise frappe.Redirect

	context.csrf_token = frappe.sessions.get_csrf_token()
	context.no_cache = 1

	status_filter = frappe.form_dict.get("status", "Submitted")
	q = (frappe.form_dict.get("q") or "").strip()
	detail_id = frappe.form_dict.get("id")

	context.current_status = status_filter
	context.search_q = q
	context.stats = get_stats()
	context.detail = None
	context.requests = []

	if detail_id:
		context.detail = load_detail(detail_id)
	else:
		context.requests = list_requests(status_filter, q)

	return context


def _human_dt(value):
	"""ISO/datetime → e.g. 14 Jul 2026, 2:30 PM."""
	if not value:
		return ""
	return format_datetime(value, "d MMM yyyy, h:mm a")


def get_stats():
	stats = {"all": 0}
	for status in ("Submitted", "Under Review", "Verified", "Rejected", "Revoked", "Draft"):
		stats[status] = frappe.db.count("Partner Verification Request", {"status": status})
		stats["all"] += stats[status]
	return stats


def list_requests(status_filter="", q=""):
	filters = {}
	if status_filter and status_filter != "all":
		filters["status"] = status_filter

	rows = frappe.get_all(
		"Partner Verification Request",
		filters=filters,
		fields=[
			"name",
			"partner",
			"partner_type",
			"status",
			"submitted_on",
			"reviewed_on",
			"creation",
			"modified",
		],
		order_by="modified desc",
		limit=100,
	)

	out = []
	q_lower = q.lower()
	for row in rows:
		full_name = frappe.db.get_value("User", row.partner, "full_name") or row.partner
		email = frappe.db.get_value("User", row.partner, "email") or ""
		if q_lower and q_lower not in (full_name or "").lower() and q_lower not in email.lower():
			continue
		row["partner_name"] = full_name
		row["partner_email"] = email
		row["submitted_on"] = _human_dt(row.get("submitted_on"))
		row["reviewed_on"] = _human_dt(row.get("reviewed_on"))
		out.append(row)
	return out


def load_detail(name):
	if not frappe.db.exists("Partner Verification Request", name):
		return None
	doc = frappe.get_doc("Partner Verification Request", name)
	full_name = frappe.db.get_value("User", doc.partner, "full_name") or doc.partner
	email = frappe.db.get_value("User", doc.partner, "email") or ""
	answers = []
	for row in doc.answers or []:
		display = ""
		if row.fieldtype in ("Text", "Long Text"):
			display = row.value_text or ""
		elif row.fieldtype in ("Int", "Decimal"):
			display = "" if row.value_number is None else str(row.value_number)
		elif row.fieldtype == "Check":
			display = "Yes" if row.value_check else "No"
		elif row.fieldtype == "Attach":
			display = row.value_file or ""
		answers.append(
			{
				"label": row.label,
				"fieldtype": row.fieldtype,
				"display": display,
				"is_file": row.fieldtype == "Attach" and bool(row.value_file),
			}
		)
	return {
		"name": doc.name,
		"partner": doc.partner,
		"partner_name": full_name,
		"partner_email": email,
		"partner_type": doc.partner_type,
		"status": doc.status,
		"rejection_reason": doc.rejection_reason or "",
		"submitted_on": _human_dt(doc.submitted_on),
		"reviewed_on": _human_dt(doc.reviewed_on),
		"reviewed_by": doc.reviewed_by,
		"answers": answers,
	}
