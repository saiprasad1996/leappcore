import frappe
from frappe.utils import now_datetime
from leappcore.backend.common.context import PageContext

def get_context(context):
    # Initialize shared context
    page_context = PageContext(context)
    context = page_context.get_context()
    
    # Prevent caching since page contains user-specific navigation
    context.no_cache = 1

    # Stats
    context.courses_count = frappe.db.count("Offering", {"active": 1})
    context.locations_count = frappe.db.count("Location")
    context.events_count = frappe.db.count("Leapp Event", {"active": 1})
    
    # Get cities from Location doctype
    context.cities = frappe.get_all(
        "Location",
        fields=["name", "city", "image"],
        order_by="city asc"
    )
    
    # Testimonials for home page
    context.testimonials = frappe.get_all(
        "Testimonials",
        filters={"active": 1},
        fields=["customer_name", "customer_designation", "description", "image"],
        limit=6,
        order_by="creation desc"
    )

    # Top Courses (Featured)
    context.top_courses = frappe.get_all(
        "Offering",
        filters={"active": 1, "featured": 1},
        fields=["name", "title", "image", "description", "duration_hours"],
        limit=5,
        order_by="creation desc"
    )

    # Upcoming Events
    context.upcoming_events = frappe.get_all(
        "Leapp Event",
        filters={"active": 1, "end_datetime": [">=", now_datetime()]},
        fields=["name", "event_name", "start_datetime", "venue_address", "featured_image"],
        limit=5,
        order_by="start_datetime asc"
    )

    return context
