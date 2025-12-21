import frappe
from frappe.exceptions import DoesNotExistError
from leappcore.backend.common.context import PageContext


def get_context(context):
    """Render event detail with live data."""
    context = PageContext(context).get_context()
    context.csrf_token = frappe.sessions.get_csrf_token()

    event_id = frappe.form_dict.get("event")
    if not event_id:
        frappe.throw("Missing event id in query string.")

    try:
        context.event = _load_event(event_id)
    except DoesNotExistError:
        # Event not found - render the 404 page
        context.show_404 = True
        context.not_found_type = "event"
        return context

    return context


def _load_event(event_id):
    """Load event details from doctype."""
    if not frappe.db.exists("Leapp Event", event_id):
        raise DoesNotExistError(f"Event '{event_id}' not found")

    event = frappe.get_doc("Leapp Event", event_id)
    
    # Get organizer details
    organizer = frappe.get_doc("User", event.organizer) if event.organizer else None
    
    # Get area details
    area = frappe.get_doc("Area", event.area) if event.area else None

    return {
        "name": event.name,
        "event_name": event.event_name,
        "heading": event.heading,
        "short_description": event.short_description,
        "long_description": event.long_description,
        "featured_image": event.featured_image,
        "start_datetime": event.start_datetime,
        "end_datetime": event.end_datetime,
        "venue_address": event.venue_address,
        "organizer": event.organizer,
        "organizer_name": organizer.full_name if organizer else "Unknown",
        "organizer_image": organizer.user_image if organizer else None,
        "area": event.area,
        "area_name": area.area_name if area else None,
        "active": event.active
    }
