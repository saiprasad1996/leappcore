import frappe
from frappe import _


def get_context(context):
    """User events page - shows events the user is interested in"""
    
    # Check if user is logged in
    if frappe.session.user == "Guest":
        # Redirect unauthenticated users to home
        frappe.local.flags.redirect_location = "/"
        raise frappe.Redirect
    
    # Check if user is a partner - redirect to partner pages
    if has_partner_role():
        frappe.local.flags.redirect_location = "/partner/event/register"
        raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Load user's interested events
    context.interested_events = get_user_interested_events()
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


def get_user_interested_events():
    """Get events the user has shown interest in"""
    interests = frappe.get_all(
        "Customer Interest",
        filters={
            "customer": frappe.session.user,
            "interest_type": "EVENT"
        },
        fields=["name", "event", "status", "creation"],
        order_by="creation desc"
    )
    
    # Enrich with event details
    events = []
    for interest in interests:
        if interest.event:
            event = frappe.get_doc("Leapp Event", interest.event)
            events.append({
                "interest_id": interest.name,
                "event_id": event.name,
                "event_name": event.event_name,
                "start_datetime": event.start_datetime,
                "end_datetime": event.end_datetime,
                "venue_address": event.venue_address,
                "organizer": event.organizer,
                "status": interest.status,
                "interested_on": interest.creation
            })
    
    return events
