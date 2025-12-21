import frappe
from frappe import _


def get_context(context):
    """Partner interests page - shows all customer interests"""
    
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/partner/interests"
        raise frappe.Redirect
    
    # Check if user has Leapp Partner role
    if not has_partner_role():
        # Redirect customers to courses page
        frappe.local.flags.redirect_location = "/courses"
        raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Get status filter
    status_filter = frappe.form_dict.get("status", "")
    
    # Load interests
    context.interests = get_partner_interests(status_filter)
    context.interest_stats = get_interest_stats()
    context.current_status = status_filter
    
    return context


def has_partner_role():
    """Check if current user has Leapp Partner role"""
    return "Leapp Partner" in frappe.get_roles(frappe.session.user)


def get_partner_interests(status_filter=""):
    """Get all interests for offerings owned by current partner"""
    filters = {
        "provider": frappe.session.user,
        "interest_type": "OFFERING"
    }
    
    if status_filter:
        filters["status"] = status_filter
    
    interests = frappe.get_all(
        "Customer Interest",
        filters=filters,
        fields=[
            "name",
            "customer",
            "offering",
            "status",
            "creation",
            "modified"
        ],
        order_by="creation desc"
    )
    
    # Enrich with customer and offering details
    for interest in interests:
        # Get customer info
        customer = frappe.get_doc("User", interest.customer)
        interest["customer_name"] = customer.full_name
        interest["customer_email"] = customer.email
        interest["customer_phone"] = customer.phone
        interest["customer_image"] = customer.user_image
        
        # Get offering info
        offering = frappe.get_doc("Offering", interest.offering)
        interest["offering_title"] = offering.title
        interest["offering_price"] = offering.price
        
        # Format dates
        interest["created_ago"] = frappe.utils.pretty_date(interest.creation)
        interest["modified_ago"] = frappe.utils.pretty_date(interest.modified)
    
    return interests


def get_interest_stats():
    """Get statistics for partner's interests"""
    partner = frappe.session.user
    
    total = frappe.db.count("Customer Interest", {
        "provider": partner,
        "interest_type": "OFFERING"
    })
    
    new = frappe.db.count("Customer Interest", {
        "provider": partner,
        "interest_type": "OFFERING",
        "status": "NEW"
    })
    
    contacted = frappe.db.count("Customer Interest", {
        "provider": partner,
        "interest_type": "OFFERING",
        "status": "CONTACTED"
    })
    
    confirmed = frappe.db.count("Customer Interest", {
        "provider": partner,
        "interest_type": "OFFERING",
        "status": "CONFIRMED"
    })
    
    return {
        "total": total,
        "new": new,
        "contacted": contacted,
        "confirmed": confirmed
    }
