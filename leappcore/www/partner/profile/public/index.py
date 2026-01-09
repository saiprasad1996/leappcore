import frappe
from frappe import _
from urllib.parse import unquote


def get_context(context):
    """Public partner profile page - viewable by anyone"""
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
    
    # Get partner identifier from URL (can be email or username)
    partner_id = frappe.form_dict.get("partner_id") or frappe.form_dict.get("id")
    
    if not partner_id:
        context.show_404 = True
        context.error_message = "Partner not specified"
        return context
    
    # URL decode the partner_id (handles special characters like +)
    partner_id = unquote(partner_id)
    
    # Try to find the user - first by exact name match, then by username
    user_name = None
    
    if frappe.db.exists("User", partner_id):
        user_name = partner_id
    else:
        # Try to find by username field
        user_by_username = frappe.db.get_value("User", {"username": partner_id}, "name")
        if user_by_username:
            user_name = user_by_username
    
    if not user_name:
        context.show_404 = True
        context.error_message = "Partner not found"
        return context
    
    # Check if user has Leapp Partner role
    partner_roles = frappe.get_roles(user_name)
    if "Leapp Partner" not in partner_roles:
        context.show_404 = True
        context.error_message = "This user is not a partner"
        return context
    
    # Load partner info
    context.partner = get_partner_info(user_name)
    context.offerings = get_partner_offerings(user_name)
    context.events = get_partner_events(user_name)
    context.stats = get_partner_stats(user_name)
    context.show_404 = False
    
    return context


def get_partner_info(partner_id):
    """Get partner user info"""
    user = frappe.get_doc("User", partner_id)
    
    # Generate a URL-safe identifier (prefer username, fallback to email)
    url_id = user.username if user.username else partner_id
    
    return {
        "name": partner_id,
        "url_id": url_id,
        "full_name": user.full_name or partner_id.split("@")[0],
        "email": user.email,
        "image": user.user_image,
        "bio": user.bio or "",
        "location": user.location or "",
        "phone": user.phone or "",
        "username": user.username or ""
    }


def get_partner_offerings(partner_id):
    """Get all active offerings by this partner"""
    offerings = frappe.get_all(
        "Offering",
        filters={
            "provider": partner_id,
            "active": 1
        },
        fields=[
            "name", "title", "subtitle", "image", "price", 
            "duration_hours", "level", "total_sessions"
        ],
        order_by="creation desc",
        limit=12
    )
    
    # Enrich with categories
    for offering in offerings:
        categories = frappe.get_all(
            "Offering Category Table",
            filters={"parent": offering.name},
            fields=["offering_category"]
        )
        offering["categories"] = [c.offering_category for c in categories]
    
    return offerings


def get_partner_events(partner_id):
    """Get upcoming events by this partner"""
    from datetime import datetime
    
    events = frappe.get_all(
        "Leapp Event",
        filters={
            "organizer": partner_id,
            "active": 1,
            "start_datetime": [">=", datetime.now()]
        },
        fields=[
            "name", "event_name", "heading", "featured_image",
            "start_datetime", "end_datetime", "venue_address", "short_description"
        ],
        order_by="start_datetime asc",
        limit=6
    )
    
    # Format dates
    for event in events:
        if event.start_datetime:
            event["formatted_date"] = event.start_datetime.strftime("%b %d, %Y")
            event["formatted_time"] = event.start_datetime.strftime("%I:%M %p")
    
    return events


def get_partner_stats(partner_id):
    """Get partner statistics"""
    total_offerings = frappe.db.count("Offering", {"provider": partner_id, "active": 1})
    total_events = frappe.db.count("Leapp Event", {"organizer": partner_id, "active": 1})
    total_interests = frappe.db.count("Customer Interest", {"provider": partner_id})
    
    return {
        "offerings": total_offerings,
        "events": total_events,
        "interests": total_interests
    }
