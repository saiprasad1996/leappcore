import frappe
from frappe import _
from frappe.utils import get_fullname, now_datetime, get_datetime


def get_context(context):
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/user/profile"
        raise frappe.Redirect
    
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
    
    # Get user information
    user = frappe.get_doc("User", frappe.session.user)
    
    # Set user data from User doctype
    context.user_email = user.email
    context.user_fullname = get_fullname(user.name) or user.email.split('@')[0]
    context.user_initial = context.user_fullname[0].upper() if context.user_fullname else "U"
    context.user_phone = user.phone
    context.user_image = user.user_image
    
    # Get or create User Profile
    profile = get_or_create_user_profile(frappe.session.user)
    
    # Set profile data
    context.profile_area = profile.area
    context.profile_address = profile.address
    context.profile_instruction_medium = profile.instruction_medium
    context.profile_about = profile.about
    context.profile_children = profile.children
    context.profile_looking_for = profile.looking_for
    context.profile_interested_in = profile.interested_in
    context.profile_theme = profile.theme
    context.profile_institution = profile.institution_name
    
    # Get areas for dropdown
    context.areas = frappe.get_all("Area", fields=["name", "area_name"], order_by="area_name")
    
    # Calculate last updated
    modified = profile.modified
    if modified:
        from frappe.utils import pretty_date
        context.last_updated = pretty_date(modified)
    else:
        context.last_updated = "recently"
    
    # Calculate profile completeness
    context.profile_completeness = calculate_profile_completeness(user, profile)
    
    # Show badge if profile is complete
    context.show_badge = context.profile_completeness >= 75
    
    # Check for success message in URL
    success = frappe.form_dict.get("success")
    if success:
        context.success_message = "Profile updated successfully!"
    
    # Handle form submission
    if frappe.request.method == "POST":
        try:
            update_profile()
            frappe.db.commit()
            # Redirect with success parameter
            frappe.local.flags.redirect_location = "/user/profile?success=1"
            raise frappe.Redirect
        except frappe.Redirect:
            # Re-raise redirect to let it pass through
            raise
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), "Profile Update Error")
            context.error_message = _("Failed to update profile. Please try again.")


def get_or_create_user_profile(user_email):
    """Get existing User Profile or create a new one"""
    profile_name = frappe.db.get_value("User Profile", {"user": user_email}, "name")
    
    if profile_name:
        return frappe.get_doc("User Profile", profile_name)
    else:
        # Create new profile
        profile = frappe.get_doc({
            "doctype": "User Profile",
            "user": user_email,
            "area": None
        })
        profile.flags.ignore_permissions = True
        profile.flags.ignore_mandatory = True
        profile.insert(ignore_permissions=True)
        frappe.db.commit()
        return profile


def calculate_profile_completeness(user, profile):
    """Calculate profile completeness percentage"""
    total_fields = 8
    completed_fields = 0
    
    # Check User doctype fields
    if user.first_name:
        completed_fields += 1
    if user.email:
        completed_fields += 1
    if user.phone:
        completed_fields += 1
        
    # Check User Profile fields
    if profile.area:
        completed_fields += 1
    if profile.address:
        completed_fields += 1
    if profile.about:
        completed_fields += 1
    if profile.institution_name:
        completed_fields += 1
    if profile.interested_in:
        completed_fields += 1
    
    return int((completed_fields / total_fields) * 100)


def update_profile():
    """Update user profile with form data"""
    user = frappe.get_doc("User", frappe.session.user)
    profile = get_or_create_user_profile(frappe.session.user)
    
    # Get form data from User fields
    full_name = frappe.form_dict.get("full_name")
    phone = frappe.form_dict.get("phone")
    
    # Get form data from User Profile fields
    area = frappe.form_dict.get("area")
    address = frappe.form_dict.get("address")
    instruction_medium = frappe.form_dict.get("instruction_medium")
    about = frappe.form_dict.get("about")
    children = frappe.form_dict.get("children")
    looking_for = frappe.form_dict.get("looking_for")
    interested_in = frappe.form_dict.get("interested_in")
    institution_name = frappe.form_dict.get("institution_name")
    
    # Update User doctype
    if full_name:
        name_parts = full_name.split(" ", 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
    if phone:
        user.phone = phone
    
    user.flags.ignore_permissions = True
    user.save()
    
    # Update User Profile doctype
    if area:
        profile.area = area
    if address:
        profile.address = address
    if instruction_medium:
        profile.instruction_medium = instruction_medium
    if about:
        profile.about = about
    if children:
        profile.children = int(children) if children else None
    if looking_for:
        profile.looking_for = looking_for
    if interested_in:
        profile.interested_in = interested_in
    if institution_name:
        profile.institution_name = institution_name
    
    profile.flags.ignore_permissions = True
    profile.save()
    
    frappe.db.commit()
