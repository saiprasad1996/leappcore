import frappe
from frappe import _


def get_context(context):
    """Render partner profile page"""
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/partner/profile"
        raise frappe.Redirect
    
    # Check if user has Leapp Partner role
    if not has_partner_role():
        # Redirect customers to courses page
        frappe.local.flags.redirect_location = "/courses"
        raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Handle form submission
    if frappe.request.method == "POST":
        try:
            save_partner_profile()
            context.success_message = _("Profile updated successfully!")
        except Exception as e:
            frappe.clear_messages()
            context.error_message = str(e)
            frappe.log_error(frappe.get_traceback(), "Partner Profile Update Error")
    
    # Load partner profile
    context.profile = load_partner_profile()
    context.user_info = get_user_info()
    context.areas = get_areas()
    
    return context


def has_partner_role():
    """Check if current user has Leapp Partner role"""
    return "Leapp Partner" in frappe.get_roles(frappe.session.user)


def load_partner_profile():
    """Load partner profile for current user"""
    user = frappe.session.user
    
    # Check if profile exists
    if frappe.db.exists("Partner Profile", user):
        profile = frappe.get_doc("Partner Profile", user)
        return profile.as_dict()
    else:
        # Return empty profile structure
        return {
            "user": user,
            "org_name": "",
            "occupation": "",
            "availability": "",
            "area": "",
            "rating": 0,
            "highest_qualification": "",
            "languages": "",
            "sample_video": ""
        }


def get_user_info():
    """Get user information"""
    user = frappe.get_doc("User", frappe.session.user)
    return {
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "user_image": user.user_image
    }


def get_areas():
    """Get list of areas"""
    areas = frappe.get_all("Area", fields=["name", "area_name"], order_by="area_name")
    return areas


def save_partner_profile():
    """Save partner profile"""
    user = frappe.session.user
    
    # Get form data
    org_name = frappe.form_dict.get("org_name")
    occupation = frappe.form_dict.get("occupation")
    availability = frappe.form_dict.get("availability")
    area = frappe.form_dict.get("area")
    highest_qualification = frappe.form_dict.get("highest_qualification")
    languages = frappe.form_dict.get("languages")
    
    # Check if profile exists
    if frappe.db.exists("Partner Profile", user):
        # Update existing profile
        profile = frappe.get_doc("Partner Profile", user)
        profile.org_name = org_name
        profile.occupation = occupation
        profile.availability = availability
        profile.area = area
        profile.highest_qualification = highest_qualification
        profile.languages = languages
        profile.save(ignore_permissions=True)
    else:
        # Create new profile
        profile = frappe.get_doc({
            "doctype": "Partner Profile",
            "user": user,
            "org_name": org_name,
            "occupation": occupation,
            "availability": availability,
            "area": area,
            "highest_qualification": highest_qualification,
            "languages": languages,
            "rating": 0
        })
        profile.insert(ignore_permissions=True)
    
    frappe.db.commit()
