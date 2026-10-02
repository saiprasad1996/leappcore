"""Cloudflare Turnstile siteverify for LEAPP public forms.

Site config keys (per deployment; never commit secrets into the app repo):
  - turnstile_site_key: public widget sitekey
  - turnstile_secret: widget secret (server-only)
  - turnstile_hostnames: comma-separated frontend hostnames for this env
    Local: leapp.local,localhost,127.0.0.1
    Preprod: preprod.leapp.co.in
    Prod: leapp.co.in,www.leapp.co.in
"""

from __future__ import annotations

import json
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import frappe
from frappe import _

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
SITEVERIFY_TIMEOUT_SECONDS = 10
MAX_TOKEN_LENGTH = 2048


def get_turnstile_site_key() -> str:
	"""Public sitekey for template embeds."""
	return (frappe.conf.get("turnstile_site_key") or "").strip()


def _expected_hostnames() -> set[str]:
	raw = frappe.conf.get("turnstile_hostnames") or ""
	return {h.strip() for h in str(raw).split(",") if h.strip()}


def _client_ip() -> Optional[str]:
	return getattr(frappe.local, "request_ip", None) or None


def verify_turnstile(expected_action: str) -> None:
	"""Fail closed unless siteverify reports success for this action and hostname."""
	secret = (frappe.conf.get("turnstile_secret") or "").strip()
	expected_hostnames = _expected_hostnames()
	token = frappe.form_dict.get("cf-turnstile-response")

	if (
		not secret
		or not expected_hostnames
		or not isinstance(token, str)
		or not token
		or len(token) > MAX_TOKEN_LENGTH
	):
		frappe.throw(
			_("Bot verification failed. Please try again."),
			frappe.ValidationError,
		)

	body = {
		"secret": secret,
		"response": token,
	}
	remoteip = _client_ip()
	if remoteip:
		body["remoteip"] = remoteip

	try:
		req = Request(
			SITEVERIFY_URL,
			data=urlencode(body).encode("utf-8"),
			headers={"Content-Type": "application/x-www-form-urlencoded"},
			method="POST",
		)
		with urlopen(req, timeout=SITEVERIFY_TIMEOUT_SECONDS) as resp:
			if getattr(resp, "status", 200) < 200 or getattr(resp, "status", 200) >= 300:
				raise HTTPError(SITEVERIFY_URL, resp.status, "siteverify non-2xx", resp.headers, None)
			result = json.loads(resp.read().decode("utf-8"))
	except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
		frappe.throw(
			_("Bot verification failed. Please try again."),
			frappe.ValidationError,
		)

	if (
		result.get("success") is not True
		or result.get("action") != expected_action
		or result.get("hostname") not in expected_hostnames
	):
		frappe.throw(
			_("Bot verification failed. Please try again."),
			frappe.ValidationError,
		)
