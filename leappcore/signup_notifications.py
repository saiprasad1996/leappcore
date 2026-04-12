"""Registration / welcome emails for Leapp Customer and Leapp Partner (manual + Google signup)."""

import frappe
from frappe import STANDARD_USERS, _
from frappe.utils import escape_html


def _role_names(user_doc) -> set[str]:
	return {r.role for r in (user_doc.roles or []) if getattr(r, "role", None)}


def user_before_insert(doc, method):
	"""Attach Leapp role for Google signup when OAuth state includes leapp_signup."""
	if doc.doctype != "User" or doc.user_type != "Website User":
		return
	signup = getattr(frappe.local, "leapp_oauth_signup", None)
	if signup not in ("customer", "partner"):
		return

	existing = _role_names(doc)
	if signup == "partner" and "Leapp Partner" not in existing:
		doc.append("roles", {"role": "Leapp Partner"})
	elif signup == "customer" and "Leapp Customer" not in existing:
		doc.append("roles", {"role": "Leapp Customer"})


def user_after_insert(doc, method):
	if doc.doctype != "User" or doc.user_type != "Website User":
		return
	# Desk / import flows run as a signed-in user; public signup and Google OAuth run as Guest.
	if frappe.session.user != "Guest":
		return
	if doc.name in STANDARD_USERS:
		return
	if getattr(doc.flags, "skip_leapp_registration_email", False):
		return

	roles = _role_names(doc)
	if "Leapp Partner" in roles:
		org = _partner_organization_from_user(doc)
		verify_url = get_verification_url(doc.name)
		send_partner_registration_email(doc.name, doc.full_name or doc.first_name or doc.email, org, verify_url)
	elif "Leapp Customer" in roles:
		verify_url = get_verification_url(doc.name)
		send_customer_registration_email(doc.name, doc.full_name or doc.first_name or doc.email, verify_url)


def _partner_organization_from_user(doc) -> str | None:
	bio = doc.bio or ""
	prefix = "Organization: "
	if bio.startswith(prefix):
		return bio[len(prefix) :].strip() or None
	return None


VERIFY_EMAIL_CACHE_PREFIX = "leapp_email_verify:"


def get_verification_url(email: str) -> str:
	"""Short website link so verification survives strict proxies and email link scanners.

	Long signed ``/api/method/...`` URLs are often rejected (413/414) or the target method is absent
	in current Frappe; a compact ``/verify-email?token=`` avoids huge wrapped URLs.
	"""
	from frappe.utils import get_url

	token = frappe.generate_hash(length=32)
	frappe.cache.set_value(
		f"{VERIFY_EMAIL_CACHE_PREFIX}{token}",
		email,
		expires_in_sec=60 * 60 * 72,
	)
	return get_url(f"/verify-email?token={token}")


def send_customer_registration_email(email: str, full_name: str, verify_url: str) -> None:
	subject = _("Welcome to LEAPP!")
	message = f"""
	<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
		<h2 style="color: #ffc700;">Welcome to LEAPP, {escape_html(full_name)}!</h2>
		<p>Thank you for joining LEAPP - your platform for learning, exploration, and personal growth.</p>
		<p>We're excited to have you as part of our community!</p>
		<p><strong>Next Steps:</strong></p>
		<ol>
			<li>Verify your email address by clicking the button below</li>
			<li>Complete your profile</li>
			<li>Start exploring courses and events</li>
		</ol>
		<div style="margin: 30px 0;">
			<a href="{verify_url}"
			   style="background-color: #ffc700; color: #000; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
				Verify Email Address
			</a>
		</div>
		<p>If you have any questions or need assistance, please don't hesitate to contact us.</p>
		<p style="margin-top: 30px;">
			Best regards,<br>
			<strong>The LEAPP Team</strong>
		</p>
		<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
		<p style="font-size: 12px; color: #666;">
			If you didn't create this account, please ignore this email or contact us at support@leapp.com
		</p>
	</div>
	"""
	_send_registration_mail(recipients=[email], subject=subject, message=message, reference_name=email)


def send_partner_registration_email(
	email: str, full_name: str, organization_name: str | None, verify_url: str
) -> None:
	subject = _("Welcome to LEAPP Partner Program!")
	org_display = escape_html(organization_name) if organization_name else str(_("your organization"))
	message = f"""
	<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
		<h2 style="color: #ffc700;">Welcome to LEAPP, {escape_html(full_name)}!</h2>
		<p>Thank you for joining the LEAPP Partner Program on behalf of <strong>{org_display}</strong>.</p>
		<p>We're excited to have you as a partner in our mission to nurture growth and inspire creativity in children.</p>
		<p><strong>Next Steps:</strong></p>
		<ol>
			<li>Verify your email address by clicking the button below</li>
			<li>Complete your partner profile</li>
			<li>Start creating and managing your offerings</li>
		</ol>
		<div style="margin: 30px 0;">
			<a href="{verify_url}"
			   style="background-color: #ffc700; color: #000; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
				Verify Email Address
			</a>
		</div>
		<p>If you have any questions or need assistance, please don't hesitate to contact us.</p>
		<p style="margin-top: 30px;">
			Best regards,<br>
			<strong>The LEAPP Team</strong>
		</p>
		<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
		<p style="font-size: 12px; color: #666;">
			If you didn't create this account, please ignore this email or contact us at support@leapp.com
		</p>
	</div>
	"""
	_send_registration_mail(recipients=[email], subject=subject, message=message, reference_name=email)


def _send_registration_mail(*, recipients: list[str], subject: str, message: str, reference_name: str) -> None:
	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			delayed=False,
			reference_doctype="User",
			reference_name=reference_name,
			now=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Leapp registration email")
