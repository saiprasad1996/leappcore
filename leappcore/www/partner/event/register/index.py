import frappe
from frappe import _
import json


def get_context(context):
    """Render event registration page"""
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/partner/event/register"
        raise frappe.Redirect
    
    # Check if user has Leapp Partner role
    if not has_partner_role():
        # Redirect customers to courses page
        frappe.local.flags.redirect_location = "/courses"
        raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Get event ID if editing
    event_id = frappe.form_dict.get("id")
    
    # Handle form submission
    if frappe.request.method == "POST":
        try:
            event_id = save_event(event_id)
            frappe.local.flags.redirect_location = f"/partner/event/register?id={event_id}&success=1"
            raise frappe.Redirect
        except Exception as e:
            frappe.clear_messages()
            context.error_message = str(e)
            frappe.log_error(frappe.get_traceback(), "Event Save Error")
    
    # Load event if editing
    if event_id:
        context.event = load_event(event_id)
        context.is_edit = True
    else:
        context.event = get_empty_event()
        context.is_edit = False
    
    # Check for success message
    if frappe.form_dict.get("success"):
        context.success_message = _("Event saved successfully!")
    
    # Load my events
    context.my_events = get_my_events()
    context.areas = get_areas()
    
    return context


def has_partner_role():
    """Check if current user has Leapp Partner role"""
    return "Leapp Partner" in frappe.get_roles(frappe.session.user)


def get_empty_event():
    """Return empty event structure"""
    return {
        "event_name": "",
        "heading": "",
        "start_datetime": "",
        "end_datetime": "",
        "venue_address": "",
        "long_description": "",
        "short_description": "",
        "area": "",
        "active": 0
    }


def load_event(event_id):
    """Load event for editing"""
    if not frappe.db.exists("Leapp Event", event_id):
        frappe.throw(_("Event not found"))
    
    event = frappe.get_doc("Leapp Event", event_id)
    
    # Check if current user is the organizer
    if event.organizer != frappe.session.user:
        frappe.throw(_("You do not have permission to edit this event"), frappe.PermissionError)
    
    return event.as_dict()


def get_my_events():
    """Get all events created by current user"""
    events = frappe.get_all(
        "Leapp Event",
        filters={"organizer": frappe.session.user},
        fields=["name", "event_name", "heading", "start_datetime", "end_datetime", "venue_address", "active", "modified"],
        order_by="start_datetime desc"
    )
    return events


def get_areas():
    """Get list of areas"""
    areas = frappe.get_all("Area", fields=["name", "area_name"], order_by="area_name")
    return areas


def save_event(event_id=None):
    """Save event"""
    user = frappe.session.user
    
    # Get form data
    event_name = frappe.form_dict.get("event_name")
    heading = frappe.form_dict.get("heading")
    start_datetime = frappe.form_dict.get("start_datetime")
    end_datetime = frappe.form_dict.get("end_datetime")
    venue_address = frappe.form_dict.get("venue_address")
    long_description = frappe.form_dict.get("long_description")
    short_description = frappe.form_dict.get("short_description")
    area = frappe.form_dict.get("area")
    active = 1 if frappe.form_dict.get("active") else 0
    
    # Validate required fields
    if not event_name:
        frappe.throw(_("Event name is required"))
    
    if event_id:
        # Update existing event
        event = frappe.get_doc("Leapp Event", event_id)
        
        # Check permission
        if event.organizer != user:
            frappe.throw(_("You do not have permission to edit this event"), frappe.PermissionError)
        
        event.event_name = event_name
        event.heading = heading
        event.start_datetime = start_datetime
        event.end_datetime = end_datetime
        event.venue_address = venue_address
        event.long_description = long_description
        event.short_description = short_description
        event.area = area
        event.active = active
        event.save(ignore_permissions=True)
    else:
        # Create new event
        event = frappe.get_doc({
            "doctype": "Leapp Event",
            "organizer": user,
            "event_name": event_name,
            "heading": heading,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "venue_address": venue_address,
            "long_description": long_description,
            "short_description": short_description,
            "area": area,
            "active": active
        })
        event.insert(ignore_permissions=True)
    
    frappe.db.commit()
    return event.name
