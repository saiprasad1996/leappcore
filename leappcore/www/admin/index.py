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
        "customers": frappe.db.count("Customer Interest"),
        "partners": frappe.db.count("Partner Profile"),
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
                {"name": "Offering", "icon": "school", "label": "Offerings"},
                {"name": "Leapp Event", "icon": "event", "label": "Events"},
                {"name": "Offering Category", "icon": "category", "label": "Categories"},
                {"name": "News & Blogs", "icon": "article", "label": "News & Blogs"},
                {"name": "FAQ", "icon": "help", "label": "FAQs"},
                {"name": "Testimonials", "icon": "stars", "label": "Testimonials"},
            ]
        },
        {
            "name": "User Management",
            "doctypes": [
                {"name": "User Profile", "icon": "person", "label": "User Profiles"},
                {"name": "Partner Profile", "icon": "groups", "label": "Partner Profiles"},
                {"name": "Customer Interest", "icon": "favorite", "label": "Customer Interests"},
                {"name": "Event Registration", "icon": "app_registration", "label": "Event Registrations"},
                {"name": "Event Claim", "icon": "verified", "label": "Event Claims"},
            ]
        },
        {
            "name": "Location & Area",
            "doctypes": [
                {"name": "Area", "icon": "map", "label": "Areas"},
                {"name": "Location", "icon": "location_on", "label": "Locations"},
            ]
        },
        {
            "name": "Website Management",
            "doctypes": [
                {"name": "Main Page", "icon": "home", "label": "Main Page"},
                {"name": "Website Menu", "icon": "menu", "label": "Website Menus"},
                {"name": "Website Submenu", "icon": "menu_open", "label": "Website Submenus"},
            ]
        },
        {
            "name": "Communication",
            "doctypes": [
                {"name": "Contact Response", "icon": "contact_mail", "label": "Contact Responses"},
                {"name": "Conversation", "icon": "chat", "label": "Conversations"},
                {"name": "Message", "icon": "mail", "label": "Messages"},
                {"name": "Fulfilment Comment", "icon": "comment", "label": "Fulfilment Comments"},
                {"name": "Partner Review", "icon": "rate_review", "label": "Partner Reviews"},
            ]
        },
        {
            "name": "System",
            "doctypes": [
                {"name": "Team", "icon": "team_dashboard", "label": "Teams"},
            ]
        }
    ]
    
    return categories
