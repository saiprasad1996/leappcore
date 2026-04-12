import frappe
from frappe import _
from frappe.utils.oauth import get_oauth_keys

from leappcore.oauth_utils import get_leapp_oauth2_authorize_url
from frappe.utils.password import get_decrypted_password


def get_context(context):
    # Redirect if already logged in
    if frappe.session.user != "Guest":
        if frappe.session.data.user_type == "Website User":
            frappe.local.flags.redirect_location = "/user/profile"
            raise frappe.Redirect
        else:
            frappe.local.flags.redirect_location = "/app"
            raise frappe.Redirect
    
    # Disable CSRF check for signup page
    frappe.flags.ignore_csrf_check = True
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # After Google signup, send customers to their profile (OAuth state redirect_to)
    context.google_login = get_google_login_info(redirect_to="/user/profile")
    
    # Handle signup form submission
    if frappe.request.method == "POST":
        try:
            signup_user()
        except frappe.Redirect:
            # Allow redirect to propagate
            raise
        except frappe.ValidationError as e:
            frappe.clear_messages()
            context.error_message = str(e)
            # Preserve form data
            context.full_name = frappe.form_dict.get("full_name", "")
            context.email = frappe.form_dict.get("email", "")
            context.phone = frappe.form_dict.get("phone", "")
            context.country_code = frappe.form_dict.get("country_code", "+91")
            return context
        except Exception as e:
            frappe.clear_messages()
            context.error_message = _("An error occurred during signup. Please try again.")
            # Preserve form data
            context.full_name = frappe.form_dict.get("full_name", "")
            context.email = frappe.form_dict.get("email", "")
            context.phone = frappe.form_dict.get("phone", "")
            context.country_code = frappe.form_dict.get("country_code", "+91")
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
            google_login["auth_url"] = get_leapp_oauth2_authorize_url(
                google_provider.name, redirect_to, signup_kind="customer"
            )
    
    return google_login


def signup_user():
    """Handle user signup"""
    from frappe.website.utils import is_signup_disabled
    
    # Check if signup is disabled
    if is_signup_disabled():
        frappe.throw(_("Sign Up is disabled"), frappe.ValidationError)
    
    # Get form data
    full_name = frappe.form_dict.get("full_name")
    email = frappe.form_dict.get("email")
    phone = frappe.form_dict.get("phone")
    country_code = frappe.form_dict.get("country_code", "+91")
    password = frappe.form_dict.get("password")
    confirm_password = frappe.form_dict.get("confirm_password")
    
    # Validate inputs
    if not full_name or not email or not password or not phone:
        frappe.throw(_("Please fill in all required fields"), frappe.ValidationError)
    
    if password != confirm_password:
        frappe.throw(_("Passwords do not match"), frappe.ValidationError)
    
    if len(password) < 8:
        frappe.throw(_("Password must be at least 8 characters long"), frappe.ValidationError)
    
    # Validate phone number (10 digits)
    if not phone.isdigit() or len(phone) != 10:
        frappe.throw(_("Please enter a valid 10-digit mobile number"), frappe.ValidationError)
    
    # Check if user already exists
    if frappe.db.exists("User", email):
        frappe.throw(_("User with this email already exists"), frappe.ValidationError)
    
    try:
        # Combine country code and phone number
        full_phone_number = f"{country_code}{phone}"
        
        # Create user
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": full_name.split()[0] if full_name else email,
            "last_name": " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
            "full_name": full_name,
            "phone": phone,
            "mobile_no": full_phone_number,  # Store with country code
            "enabled": 1,
            "new_password": password,
            "user_type": "Website User",
            "send_welcome_email": 0
        })
        
        # Add Leapp Customer role
        user.append("roles", {
            "role": "Leapp Customer"
        })
        
        # Save the user
        user.flags.ignore_permissions = True
        user.insert(ignore_permissions=True)
        
        frappe.db.commit()

        # Redirect to home page
        frappe.local.flags.redirect_location = "/"
        raise frappe.Redirect
        
    except frappe.Redirect:
        # Allow redirect to propagate without rollback
        raise
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "User Signup Error")
        raise


