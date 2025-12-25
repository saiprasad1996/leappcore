import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
from frappe.utils.password import get_decrypted_password


def get_context(context):
    # Redirect if already logged in
    if frappe.session.user != "Guest":
        if frappe.session.data.user_type == "Website User":
            frappe.local.flags.redirect_location = "/"
            raise frappe.Redirect
        else:
            frappe.local.flags.redirect_location = "/app"
            raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Get redirect URL if provided
    redirect_to = frappe.local.request.args.get("redirect-to")
    
    # Setup Google login
    context.google_login = get_google_login_info(redirect_to)
    
    # Handle login form submission
    if frappe.request.method == "POST":
        try:
            login_user()
        except frappe.AuthenticationError:
            frappe.clear_messages()
            context.error_message = _("Invalid login credentials")
            return context


def get_google_login_info(redirect_to=None):
    """Get Google login configuration"""
    google_login = {
        "enabled": False,
        "auth_url": None,
        "provider_name": "Google"
    }
    
    # Check if Google login is configured
    google_provider = frappe.db.get_value(
        "Social Login Key",
        filters={
            "enable_social_login": 1,
            "provider_name": "Google"
        },
        fieldname=["name", "client_id", "base_url", "provider_name"],
        as_dict=True
    )
    
    if google_provider:
        # Check if client secret is configured
        client_secret = get_decrypted_password(
            "Social Login Key",
            google_provider.name,
            "client_secret",
            raise_exception=False
        )
        
        # Check if OAuth keys are properly configured
        if google_provider.client_id and google_provider.base_url and client_secret and get_oauth_keys(google_provider.name):
            google_login["enabled"] = True
            google_login["auth_url"] = get_oauth2_authorize_url(google_provider.name, redirect_to)
    
    return google_login


def login_user():
    """Handle user login"""
    from frappe.auth import LoginManager
    
    # Get credentials from form
    usr = frappe.form_dict.get("usr")
    pwd = frappe.form_dict.get("pwd")
    
    if not usr or not pwd:
        frappe.throw(_("Please enter username and password"), frappe.AuthenticationError)
    
    # Authenticate user
    login_manager = LoginManager()
    login_manager.authenticate(user=usr, pwd=pwd)
    login_manager.post_login()
    
    # Redirect based on user type
    if frappe.response.get("message") == "Logged In":
        frappe.local.flags.redirect_location = "/"
    elif frappe.response.get("message") == "No App":
        frappe.local.flags.redirect_location = "/"
    else:
        frappe.local.flags.redirect_location = "/"
    
    raise frappe.Redirect
