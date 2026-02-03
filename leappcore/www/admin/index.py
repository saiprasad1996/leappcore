import frappe
from frappe import _


def get_context(context):
    """Admin page context - only accessible to Administrator and System Manager"""
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/admin"
        raise frappe.Redirect
    
    # Check if user has Administrator or System Manager role
    user_roles = frappe.get_roles(frappe.session.user)
    if "Administrator" not in user_roles and "System Manager" not in user_roles:
        frappe.local.flags.redirect_location = "/"
        raise frappe.Redirect
    
    context.no_cache = 1
    
    # Get analytics data
    context.analytics = get_analytics_data()
    
    # Get doctype shortcuts organized by category
    context.doctype_categories = get_doctype_categories()
    
    return context


def get_analytics_data():
    """Fetch analytics counts for dashboard cards"""
    analytics = {
        "customers": frappe.db.count("User", filters=[
            ["Has Role", "role", "=", "Leapp Customer"]
        ]),
        "partners": frappe.db.count("User", filters=[
            ["Has Role", "role", "=", "Leapp Partner"]
        ]),
        "offerings": frappe.db.count("Offering"),
        "events": frappe.db.count("Leapp Event")
    }
    return analytics


def get_doctype_categories():
    """Define doctype categories with icons and metadata"""
    categories = [
        {
            "name": "Content Management",
            "doctypes": [
                {"name": "Offering", "icon": "school", "label": "Offerings", "href": "/app/offering"},
                {"name": "Leapp Event", "icon": "event", "label": "Events", "href": "/app/leapp-event"},
                {"name": "Offering Category", "icon": "category", "label": "Categories", "href": "/app/offering-category"},
                {"name": "News & Blogs", "icon": "article", "label": "News & Blogs", "href": "/app/newsblogs"},
                {"name": "FAQ", "icon": "help", "label": "FAQs", "href": "/app/faq"},
                {"name": "Testimonials", "icon": "stars", "label": "Testimonials", "href": "/app/testimonials"},
            ]
        },
        {
            "name": "User Management",
            "doctypes": [
                {"name": "User Profile", "icon": "person", "label": "User Profiles", "href": "/desk/user?enabled=1&role=Leapp+Customer"},
                {"name": "Partner Profile", "icon": "groups", "label": "Partner Profiles", "href": "/desk/user?enabled=1&role=Leapp+Partner"},
                {"name": "Customer Interest", "icon": "favorite", "label": "Customer Interests", "href": "/partner/interests"},
                {"name": "Event Registration", "icon": "app_registration", "label": "Event Registrations", "href": "/app/event-registration"},
                {"name": "Event Claim", "icon": "verified", "label": "Event Claims", "href": "/app/event-claim"},
            ]
        },
        {
            "name": "Location & Area",
            "doctypes": [
                {"name": "Area", "icon": "map", "label": "Areas", "href": "/app/area"},
                {"name": "Location", "icon": "location_on", "label": "Locations", "href": "/app/location"},
            ]
        },
        {
            "name": "Website Management",
            "doctypes": [
                {"label": "Main Page", "icon": "home", "href": "/app/main-page"},
                {"label": "About Page", "icon": "info", "href": "/app/about-page"},
                {"label": "Team", "icon": "groups", "href": "/app/team"},
                {"label": "Testimonials", "icon": "star", "href": "/app/testimonials"},
            ]
        },
        {
            "name": "Communication",
            "doctypes": [
                {"name": "Contact Response", "icon": "contact_mail", "label": "Contact Responses", "href": "/app/contactresponse"},
                # {"name": "Conversation", "icon": "chat", "label": "Conversations", "href": "/app/conversation"},
                {"name": "Message", "icon": "mail", "label": "Messages", "href": "/app/message"},
                {"name": "Fulfilment Comment", "icon": "comment", "label": "Fulfilment Comments", "href": "/app/fulfilment-comment"},
                {"name": "Partner Review", "icon": "rate_review", "label": "Partner Reviews", "href": "/app/partner-review"},
            ]
        },
        {
            "name": "System",
            "doctypes": [
                {"name": "Team", "icon": "team_dashboard", "label": "Teams", "href": "/app/team"},
            ]
        }
    ]
    
    return categories
