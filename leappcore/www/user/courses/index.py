import frappe
from frappe import _


def get_context(context):
    """User courses page - shows courses enrolled by the user"""
    
    # Check if user is logged in
    if frappe.session.user == "Guest":
        # Redirect unauthenticated users to home
        frappe.local.flags.redirect_location = "/"
        raise frappe.Redirect
    
    # Check if user is a partner - redirect to partner pages
    if has_partner_role():
        frappe.local.flags.redirect_location = "/partner/offering/register"
        raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Get view mode (grid or list)
    view_mode = frappe.form_dict.get("view", "grid")
    context.view_mode = view_mode
    
    # Load user's enrolled courses
    context.enrolled_courses = get_user_enrolled_courses()
    context.user_info = get_user_info()
    
    return context


def has_partner_role():
    """Check if current user has Leapp Partner role"""
    return "Leapp Partner" in frappe.get_roles(frappe.session.user)


def get_user_info():
    """Get current user information"""
    user = frappe.get_doc("User", frappe.session.user)
    return {
        "full_name": user.full_name,
        "email": user.email,
        "user_image": user.user_image
    }


def get_user_enrolled_courses():
    """Get courses the user is enrolled in / interested in"""
    interests = frappe.get_all(
        "Customer Interest",
        filters={
            "customer": frappe.session.user,
            "interest_type": "OFFERING"
        },
        fields=["name", "offering", "status", "creation"],
        order_by="creation desc"
    )
    
    # Enrich with offering details
    courses = []
    for interest in interests:
        if interest.offering:
            offering = frappe.get_doc("Offering", interest.offering)
            
            # Get categories
            categories = frappe.get_all(
                "Offering Category Table",
                filters={"parent": offering.name},
                fields=["offering_category"],
                pluck="offering_category"
            )
            
            courses.append({
                "interest_id": interest.name,
                "offering_id": offering.name,
                "title": offering.title,
                "subtitle": offering.subtitle,
                "description": offering.description,
                "image": offering.image,
                "price": offering.price,
                "duration_hours": offering.duration_hours,
                "level": offering.level,
                "provider": offering.provider,
                "status": interest.status,
                "interested_on": interest.creation,
                "categories": categories,
                "detail_url": f"/courses/detail?offering={offering.name}"
            })
    
    return courses

