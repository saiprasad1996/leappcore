import frappe
from frappe import _
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
    
    # Handle signup form submission
    if frappe.request.method == "POST":
        try:
            signup_user()
        except frappe.ValidationError as e:
            frappe.clear_messages()
            context.error_message = str(e)
            return context
        except Exception as e:
            frappe.clear_messages()
            context.error_message = _("An error occurred during signup. Please try again.")
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


def signup_user():
    """Handle user signup"""
    from frappe.core.doctype.user.user import sign_up
    from frappe.website.utils import is_signup_disabled
    
    # Check if signup is disabled
    if is_signup_disabled():
        frappe.throw(_("Sign Up is disabled"), frappe.ValidationError)
    
    # Get form data
    full_name = frappe.form_dict.get("full_name")
    email = frappe.form_dict.get("email")
    password = frappe.form_dict.get("password")
    confirm_password = frappe.form_dict.get("confirm_password")
    
    # Validate inputs
    if not full_name or not email or not password:
        frappe.throw(_("Please fill in all required fields"), frappe.ValidationError)
    
    if password != confirm_password:
        frappe.throw(_("Passwords do not match"), frappe.ValidationError)
    
    if len(password) < 8:
        frappe.throw(_("Password must be at least 8 characters long"), frappe.ValidationError)
    
    # Get redirect URL
    redirect_to = frappe.form_dict.get("redirect_to") or "/"
    
    # Call Frappe's sign_up function
    status, message = sign_up(email, full_name, redirect_to)
    
    if status == 0:
        frappe.throw(message, frappe.ValidationError)
    elif status == 1:
        # Email verification required
        frappe.local.flags.redirect_location = "/signup-success?message=" + frappe.utils.quote(message)
        raise frappe.Redirect
    elif status == 2:
        # Admin verification required
        frappe.local.flags.redirect_location = "/signup-success?message=" + frappe.utils.quote(message)
        raise frappe.Redirect
