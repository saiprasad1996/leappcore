import json

import frappe
from frappe.utils import formatdate, now_datetime
from leappcore.backend.common.context import PageContext
from leappcore.backend.common.offering_cards import enrich_offerings_for_cards

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
    
    # Featured locations for "Explore Cities" (ordered by Location.order ascending)
    context.cities = frappe.db.sql(
        """
        SELECT name, city, image
        FROM `tabLocation`
        WHERE COALESCE(featured, 0) = 1
        ORDER BY IFNULL(`order`, 2147483647) ASC, city ASC
        """,
        as_dict=True,
    )
    
    # Testimonials for home page
    context.testimonials = frappe.get_all(
        "Testimonials",
        filters={"active": 1},
        fields=[
            "customer_name",
            "customer_designation",
            "testimonial_title",
            "description",
            "image",
            "creation",
        ],
        limit=6,
        order_by="creation desc",
    )
    for t in context.testimonials:
        t["posted_date"] = formatdate(t["creation"], "medium") if t.get("creation") else ""
    context.testimonials_json = json.dumps(context.testimonials, default=str)

    # Top Courses (Featured)
    context.top_courses = frappe.get_all(
        "Offering",
        filters={"active": 1, "featured": 1},
        fields=["name", "title", "subtitle", "image", "duration_hours", "price", "negotiable"],
        order_by="creation desc",
    )
    enrich_offerings_for_cards(context.top_courses)

    # Upcoming Events
    context.upcoming_events = frappe.get_all(
        "Leapp Event",
        filters={"active": 1, "end_datetime": [">=", now_datetime()]},
        fields=["name", "event_name", "start_datetime", "venue_address", "featured_image"],
        order_by="start_datetime asc"
    )

    context.news_and_blogs = frappe.get_all(
        "NewsBlogs",
        filters={"published": 1},
        fields=["name", "title", "image", "author", "creation"],
        limit=5,
        order_by="creation desc"
    )

    return context
