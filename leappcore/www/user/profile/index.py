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
    
    # Set user data
    context.user_email = user.email
    context.user_fullname = get_fullname(user.name) or user.email.split('@')[0]
    context.user_initial = context.user_fullname[0].upper() if context.user_fullname else "U"
    
    # Get custom user fields (you may need to adjust these based on your User doctype customizations)
    context.user_age = user.get("age") if hasattr(user, "age") else None
    context.user_grade = user.get("grade") if hasattr(user, "grade") else None
    context.user_school = user.get("school") if hasattr(user, "school") else None
    
    # Calculate last updated
    modified = user.modified
    if modified:
        from frappe.utils import pretty_date
        context.last_updated = pretty_date(modified)
    else:
        context.last_updated = "recently"
    
    # Calculate profile completeness
    context.profile_completeness = calculate_profile_completeness(user)
    
    # Show badge if profile is complete
    context.show_badge = context.profile_completeness >= 75
    
    # Handle form submission
    if frappe.request.method == "POST":
        try:
            update_profile()
            frappe.msgprint(_("Profile updated successfully"), indicator="green")
            frappe.local.flags.redirect_location = "/user/profile"
            raise frappe.Redirect
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Profile Update Error")
            context.error_message = str(e)


def calculate_profile_completeness(user):
    """Calculate profile completeness percentage"""
    total_fields = 6
    completed_fields = 0
    
    # Check basic fields
    if user.first_name:
        completed_fields += 1
    if user.email:
        completed_fields += 1
    if user.get("age"):
        completed_fields += 1
    if user.get("grade"):
        completed_fields += 1
    if user.get("school"):
        completed_fields += 1
    if user.user_image:
        completed_fields += 1
    
    return int((completed_fields / total_fields) * 100)


def update_profile():
    """Update user profile with form data"""
    user = frappe.get_doc("User", frappe.session.user)
    
    # Get form data
    full_name = frappe.form_dict.get("full_name")
    age = frappe.form_dict.get("age")
    grade = frappe.form_dict.get("grade")
    school = frappe.form_dict.get("school")
    
    # Update basic fields
    if full_name:
        name_parts = full_name.split(" ", 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
    
    # Update custom fields (you may need to add these fields to User doctype)
    if hasattr(user, "age"):
        user.age = age
    if hasattr(user, "grade"):
        user.grade = grade
    if hasattr(user, "school"):
        user.school = school
    
    user.flags.ignore_permissions = True
    user.save()
    frappe.db.commit()
