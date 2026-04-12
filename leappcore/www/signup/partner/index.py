import frappe
from frappe import _
from frappe.utils.oauth import get_oauth_keys

from leappcore.oauth_utils import get_leapp_oauth2_authorize_url
from frappe.utils.password import get_decrypted_password


def get_context(context):
    # Redirect if already logged in
    if frappe.session.user != "Guest":
        if frappe.session.data.user_type == "Website User":
            frappe.local.flags.redirect_location = "/partner/profile"
            raise frappe.Redirect
        else:
            frappe.local.flags.redirect_location = "/app"
            raise frappe.Redirect
    
    # Disable CSRF check for signup page
    frappe.flags.ignore_csrf_check = True
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Post–Google OAuth redirect (Frappe uses /me if this is missing)
    redirect_to = frappe.local.request.args.get("redirect-to") or "/partner/profile"

    context.google_login = get_google_login_info(redirect_to)
    
    # Handle signup form submission
    if frappe.request.method == "POST":
        try:
            signup_partner()
        except frappe.Redirect:
            raise
        except frappe.ValidationError as e:
            frappe.clear_messages()
            context.error_message = str(e)
            context.full_name = frappe.form_dict.get("full_name", "")
            context.email = frappe.form_dict.get("email", "")
            context.phone = frappe.form_dict.get("phone", "")
            context.country_code = frappe.form_dict.get("country_code", "+91")
            context.organization_name = frappe.form_dict.get("organization_name", "")
            context.city = frappe.form_dict.get("city", "")
            context.address = frappe.form_dict.get("address", "")
            return context
        except Exception as e:
            frappe.clear_messages()
            context.error_message = _("An error occurred during signup. Please try again.")
            context.full_name = frappe.form_dict.get("full_name", "")
            context.email = frappe.form_dict.get("email", "")
            context.phone = frappe.form_dict.get("phone", "")
            context.country_code = frappe.form_dict.get("country_code", "+91")
            context.organization_name = frappe.form_dict.get("organization_name", "")
            context.city = frappe.form_dict.get("city", "")
            context.address = frappe.form_dict.get("address", "")
            frappe.log_error(frappe.get_traceback(), "Partner Signup Error")
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
                google_provider.name, redirect_to, signup_kind="partner"
            )
    
    return google_login


def signup_partner():
    """Handle partner signup"""
    from frappe.website.utils import is_signup_disabled
    
    # Check if signup is disabled
    if is_signup_disabled():
        frappe.throw(_("Sign Up is disabled"), frappe.ValidationError)
    
    # Get form data
    full_name = frappe.form_dict.get("full_name")
    email = frappe.form_dict.get("email")
    password = frappe.form_dict.get("password")
    confirm_password = frappe.form_dict.get("confirm_password")
    organization_name = frappe.form_dict.get("organization_name")
    phone = frappe.form_dict.get("phone")
    country_code = frappe.form_dict.get("country_code", "+91")
    address = frappe.form_dict.get("address")
    city = frappe.form_dict.get("city")
    
    # Validate inputs
    if not full_name or not email or not password or not organization_name:
        frappe.throw(_("Please fill in all required fields"), frappe.ValidationError)
    
    if password != confirm_password:
        frappe.throw(_("Passwords do not match"), frappe.ValidationError)
    
    if len(password) < 8:
        frappe.throw(_("Password must be at least 8 characters long"), frappe.ValidationError)
    
    # Check if user already exists
    if frappe.db.exists("User", email):
        frappe.throw(_("User with this email already exists"), frappe.ValidationError)
    
    try:
        # Create user with full phone number
        full_phone = f"{country_code}{phone}" if phone else None
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": full_name.split()[0] if full_name else email,
            "last_name": " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
            "full_name": full_name,
            "enabled": 1,
            "new_password": password,
            "user_type": "Website User",
            "send_welcome_email": 0,
            "phone": phone,
            "mobile_no": full_phone,
        })
        
        # Add Leapp Partner role
        user.append("roles", {
            "role": "Leapp Partner"
        })
        
        # Save the user
        user.flags.ignore_permissions = True
        user.insert(ignore_permissions=True)
        
        # Create a Partner profile document if you have a Partner doctype
        # Uncomment and modify if you have a Partner doctype
        # partner_profile = frappe.get_doc({
        #     "doctype": "Partner",
        #     "user": user.name,
        #     "organization_name": organization_name,
        #     "phone": phone,
        #     "address": address,
        #     "city": city,
        # })
        # partner_profile.insert(ignore_permissions=True)
        
        # Store additional partner information in User document custom fields
        # Or you can create a separate Partner Profile doctype
        frappe.db.set_value("User", user.name, {
            "bio": f"Organization: {organization_name}",
            # Add more custom fields as needed
        }, update_modified=False)
        
        frappe.db.commit()

        # Redirect to success page
        success_message = _("Your partner account has been created successfully! Please check your email to verify your account.")
        frappe.local.flags.redirect_location = "/signup-success?message=" + frappe.utils.quote(success_message)
        raise frappe.Redirect
        
    except frappe.Redirect:
        raise
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Partner Signup Error")
        raise


