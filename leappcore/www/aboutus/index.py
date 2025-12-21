import frappe


def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    
    # Main Page Data
    context.main_page = frappe.get_single("Main Page")
    
    # Team Members
    context.team_members = frappe.get_all(
        "Team",
        filters={"active": 1},
        fields=["member_name", "position", "image", "description"],
        order_by="creation asc"
    )
    
    # Testimonials
    context.testimonials = frappe.get_all(
        "Testimonials",
        filters={"active": 1},
        fields=["customer_name", "customer_designation", "testimonial_title", "description", "image"],
        order_by="creation desc"
    )
