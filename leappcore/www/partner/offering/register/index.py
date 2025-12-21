import frappe
from frappe import _
import json


def get_context(context):
    """Render offering registration page"""
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/partner/offering/register"
        raise frappe.Redirect
    
    # Check if user has Leapp Partner role
    if not has_partner_role():
        # Redirect customers to courses page
        frappe.local.flags.redirect_location = "/courses"
        raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Get offering ID if editing
    offering_id = frappe.form_dict.get("id")
    
    # Handle form submission
    if frappe.request.method == "POST":
        try:
            offering_id = save_offering(offering_id)
            frappe.local.flags.redirect_location = f"/partner/offering/register?id={offering_id}&success=1"
            raise frappe.Redirect
        except Exception as e:
            frappe.clear_messages()
            context.error_message = str(e)
            frappe.log_error(frappe.get_traceback(), "Offering Save Error")
    
    # Load offering if editing
    if offering_id:
        context.offering = load_offering(offering_id)
        context.is_edit = True
    else:
        context.offering = get_empty_offering()
        context.is_edit = False
    
    # Check for success message
    if frappe.form_dict.get("success"):
        context.success_message = _("Offering saved successfully!")
    
    # Load my offerings
    context.my_offerings = get_my_offerings()
    context.categories = get_categories()
    
    return context


def has_partner_role():
    """Check if current user has Leapp Partner role"""
    return "Leapp Partner" in frappe.get_roles(frappe.session.user)


def get_empty_offering():
    """Return empty offering structure"""
    return {
        "title": "",
        "subtitle": "",
        "description": "",
        "image": "",
        "price": 0,
        "duration_hours": 0,
        "level": "Beginner",
        "total_sessions": 0,
        "active": 0,
        "featured": 0
    }


def load_offering(offering_id):
    """Load offering for editing"""
    if not frappe.db.exists("Offering", offering_id):
        frappe.throw(_("Offering not found"))
    
    offering = frappe.get_doc("Offering", offering_id)
    
    # Check if current user is the provider
    if offering.provider != frappe.session.user:
        frappe.throw(_("You do not have permission to edit this offering"), frappe.PermissionError)
    
    return offering.as_dict()


def get_my_offerings():
    """Get all offerings created by current user"""
    offerings = frappe.get_all(
        "Offering",
        filters={"provider": frappe.session.user},
        fields=["name", "title", "subtitle", "price", "active", "featured", "modified"],
        order_by="modified desc"
    )
    return offerings


def get_categories():
    """Get all offering categories"""
    categories = frappe.get_all(
        "Offering Category",
        fields=["name", "category_name"],
        order_by="category_name"
    )
    return categories


def save_offering(offering_id=None):
    """Save offering"""
    user = frappe.session.user
    
    # Get form data
    title = frappe.form_dict.get("title")
    subtitle = frappe.form_dict.get("subtitle")
    description = frappe.form_dict.get("description")
    price = frappe.form_dict.get("price", 0)
    duration_hours = frappe.form_dict.get("duration_hours", 0)
    level = frappe.form_dict.get("level", "Beginner")
    total_sessions = frappe.form_dict.get("total_sessions", 0)
    active = 1 if frappe.form_dict.get("active") else 0
    
    # Validate required fields
    if not title:
        frappe.throw(_("Title is required"))
    
    if offering_id:
        # Update existing offering
        offering = frappe.get_doc("Offering", offering_id)
        
        # Check permission
        if offering.provider != user:
            frappe.throw(_("You do not have permission to edit this offering"), frappe.PermissionError)
        
        offering.title = title
        offering.subtitle = subtitle
        offering.description = description
        offering.price = price
        offering.duration_hours = duration_hours
        offering.level = level
        offering.total_sessions = total_sessions
        offering.active = active
        offering.save(ignore_permissions=True)
    else:
        # Create new offering
        offering = frappe.get_doc({
            "doctype": "Offering",
            "provider": user,
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "price": price,
            "duration_hours": duration_hours,
            "level": level,
            "total_sessions": total_sessions,
            "active": active,
            "featured": 0
        })
        offering.insert(ignore_permissions=True)
    
    frappe.db.commit()
    return offering.name
