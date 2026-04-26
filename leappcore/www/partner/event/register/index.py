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
        except frappe.Redirect:
            raise
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
    context.locations = get_locations()
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
        "featured_image": "",
        "area": "",
        "area_name": "",
        "location": "",
        "location_display": "",
        "active": 0,
    }


def load_event(event_id):
    """Load event for editing"""
    if not frappe.db.exists("Leapp Event", event_id):
        frappe.throw(_("Event not found"))
    
    event = frappe.get_doc("Leapp Event", event_id)
    
    # Check if current user is the organizer
    if event.organizer != frappe.session.user:
        frappe.throw(_("You do not have permission to edit this event"), frappe.PermissionError)
    
    data = event.as_dict()
    
    # Convert datetime to string for HTML inputs
    if data.get("start_datetime"):
        data["start_datetime"] = str(data["start_datetime"]).replace(" ", "T")[:16]
    if data.get("end_datetime"):
        data["end_datetime"] = str(data["end_datetime"]).replace(" ", "T")[:16]
    
    # Area display + city (location) for form
    data["location"] = data.get("location") or ""
    data["location_display"] = ""
    if data.get("location"):
        data["location_display"] = (
            frappe.db.get_value("Location", data["location"], "city") or data["location"]
        )
    elif data.get("area") and frappe.db.exists("Area", data["area"]):
        loc = frappe.db.get_value("Area", data["area"], "location")
        if loc:
            data["location"] = loc
            data["location_display"] = (
                frappe.db.get_value("Location", loc, "city") or loc
            )

    if data.get("area") and frappe.db.exists("Area", data["area"]):
        data["area_name"] = frappe.db.get_value("Area", data["area"], "area_name") or ""
    else:
        data["area_name"] = ""

    return data


def get_locations():
    """Cities / locations for filtering areas (same as offering register)."""
    return frappe.get_all(
        "Location",
        fields=["name", "city"],
        order_by="city asc",
    )


def get_areas():
    """All areas with parent Location name for client-side filtering."""
    return frappe.get_all(
        "Area",
        fields=["name", "area_name", "location"],
        order_by="area_name asc",
    )


def get_my_events():
    """Get all events created by current user"""
    events = frappe.get_all(
        "Leapp Event",
        filters={"organizer": frappe.session.user},
        fields=["name", "event_name", "heading", "start_datetime", "end_datetime", "venue_address", "active", "modified"],
        order_by="start_datetime desc"
    )
    return events


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
    location = (frappe.form_dict.get("location") or "").strip()
    area = (frappe.form_dict.get("area") or "").strip()
    active = 1 if frappe.form_dict.get("active") else 0

    if area and not location:
        location = frappe.db.get_value("Area", area, "location") or ""
    if area and location:
        area_loc = frappe.db.get_value("Area", area, "location")
        if area_loc != location:
            frappe.throw(_("Selected area does not belong to the selected city."))
    
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
        event.start_datetime = start_datetime if start_datetime else None
        event.end_datetime = end_datetime if end_datetime else None
        event.venue_address = venue_address
        event.long_description = long_description
        event.short_description = short_description
        event.location = location or None
        event.area = area or None
        event.active = active
    else:
        # Create new event
        event = frappe.get_doc({
            "doctype": "Leapp Event",
            "organizer": user,
            "event_name": event_name,
            "heading": heading,
            "start_datetime": start_datetime if start_datetime else None,
            "end_datetime": end_datetime if end_datetime else None,
            "venue_address": venue_address,
            "long_description": long_description,
            "short_description": short_description,
            "location": location or None,
            "area": area or None,
            "active": active,
        })

    # Persist first so `event.name` exists — File requires attached_to_name as str/int
    if event_id:
        event.save(ignore_permissions=True)
    else:
        event.insert(ignore_permissions=True)

    if frappe.request.files.get("featured_image"):
        file = frappe.request.files.get("featured_image")
        if file.filename:
            from frappe.utils.file_manager import save_file

            saved_file = save_file(
                file.filename,
                file.read(),
                "Leapp Event",
                event.name,
                folder="Home/Attachments",
                is_private=0,
            )
            event.featured_image = saved_file.file_url
            event.save(ignore_permissions=True)

    frappe.db.commit()
    return event.name
