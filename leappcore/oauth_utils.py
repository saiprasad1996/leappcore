"""OAuth helpers: signup context in state + patch so User hooks can read it during Google signup."""

import base64
import json

import frappe
from frappe.utils.oauth import get_oauth2_flow, get_oauth2_providers, get_redirect_uri


def get_leapp_oauth2_authorize_url(provider: str, redirect_to: str, signup_kind: str | None = None) -> str:
	"""Like frappe.utils.oauth.get_oauth2_authorize_url but adds optional leapp_signup to OAuth state."""
	flow = get_oauth2_flow(provider)

	state = {
		"site": frappe.utils.get_url(),
		"token": frappe.generate_hash(),
		"redirect_to": redirect_to,
	}
	if signup_kind in ("customer", "partner"):
		state["leapp_signup"] = signup_kind

	data = {
		"redirect_uri": get_redirect_uri(provider),
		"state": base64.b64encode(bytes(json.dumps(state).encode("utf-8"))),
	}

	oauth2_providers = get_oauth2_providers()
	data.update(oauth2_providers[provider].get("auth_url_data", {}))

	return flow.get_authorize_url(**data)


def patch_login_oauth_user_for_signup_context():
	"""Expose decoded OAuth state.leapp_signup on frappe.local during login_oauth_user (for User hooks)."""
	from frappe.utils import oauth as oauth_mod

	if getattr(oauth_mod.login_oauth_user, "_leapp_signup_patch", False):
		return

	_original = oauth_mod.login_oauth_user

	def login_oauth_user(data, *, provider=None, state=None, generate_login_token=False):
		signup = None
		try:
			st = state
			if isinstance(st, str):
				st = json.loads(base64.b64decode(st).decode("utf-8"))
			if isinstance(st, dict):
				signup = st.get("leapp_signup")
		except Exception:
			signup = None

		frappe.local.leapp_oauth_signup = signup
		try:
			return _original(data, provider=provider, state=state, generate_login_token=generate_login_token)
		finally:
			frappe.local.leapp_oauth_signup = None

	login_oauth_user._leapp_signup_patch = True
	oauth_mod.login_oauth_user = login_oauth_user
