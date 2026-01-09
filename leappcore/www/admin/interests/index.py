import frappe
from frappe import _


def get_context(context):
    """Admin interests page - shows ALL customer interests for administrators"""
    
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/admin/interests"
        raise frappe.Redirect
    
    user_roles = frappe.get_roles(frappe.session.user)
    
    # Only allow Administrator or System Manager
    if frappe.session.user != "Administrator" and "System Manager" not in user_roles:
        # Check if they're a partner
        if "Leapp Partner" in user_roles:
            frappe.local.flags.redirect_location = "/partner/interests"
            raise frappe.Redirect
        else:
            # Regular customer - redirect to profile
            frappe.local.flags.redirect_location = "/user/profile"
            raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Get filters
    status_filter = frappe.form_dict.get("status", "")
    provider_filter = frappe.form_dict.get("provider", "")
    
    # Load ALL interests
    context.interests = get_all_interests(status_filter, provider_filter)
    context.interest_stats = get_all_interest_stats()
    context.current_status = status_filter
    context.current_provider = provider_filter
    
    # Load list of providers for filter dropdown
    context.providers = get_all_providers()
    
    return context


def get_all_interests(status_filter="", provider_filter=""):
    """Get ALL customer interests across all providers"""
    filters = {"interest_type": "OFFERING"}
    
    if status_filter:
        filters["status"] = status_filter
    
    if provider_filter:
        filters["provider"] = provider_filter
    
    interests = frappe.get_all(
        "Customer Interest",
        filters=filters,
        fields=[
            "name",
            "customer",
            "provider",
            "offering",
            "status",
            "creation",
            "modified"
        ],
        order_by="creation desc",
        limit=100
    )
    
    # Enrich with customer, provider and offering details
    for interest in interests:
        # Get customer info
        try:
            customer = frappe.get_doc("User", interest.customer)
            interest["customer_name"] = customer.full_name or interest.customer
            interest["customer_email"] = customer.email
            interest["customer_phone"] = customer.phone
            interest["customer_image"] = customer.user_image
        except:
            interest["customer_name"] = interest.customer
            interest["customer_email"] = interest.customer
            interest["customer_phone"] = ""
            interest["customer_image"] = ""
        
        # Get provider info
        try:
            provider = frappe.get_doc("User", interest.provider)
            interest["provider_name"] = provider.full_name or interest.provider
            interest["provider_email"] = provider.email
        except:
            interest["provider_name"] = interest.provider
            interest["provider_email"] = interest.provider
        
        # Get offering info
        try:
            offering = frappe.get_doc("Offering", interest.offering)
            interest["offering_title"] = offering.title
            interest["offering_price"] = offering.price
        except:
            interest["offering_title"] = "Unknown Offering"
            interest["offering_price"] = 0
        
        # Format dates
        interest["created_ago"] = frappe.utils.pretty_date(interest.creation)
        interest["modified_ago"] = frappe.utils.pretty_date(interest.modified)
    
    return interests


def get_all_interest_stats():
    """Get global statistics for all interests"""
    total = frappe.db.count("Customer Interest", {"interest_type": "OFFERING"})
    interested = frappe.db.count("Customer Interest", {"interest_type": "OFFERING", "status": "INTERESTED"})
    contacted = frappe.db.count("Customer Interest", {"interest_type": "OFFERING", "status": "CONTACTED"})
    in_progress = frappe.db.count("Customer Interest", {"interest_type": "OFFERING", "status": "IN_PROGRESS"})
    confirmed = frappe.db.count("Customer Interest", {"interest_type": "OFFERING", "status": "CONFIRMED"})
    closed = frappe.db.count("Customer Interest", {"interest_type": "OFFERING", "status": "CLOSED"})
    
    return {
        "total": total,
        "interested": interested,
        "contacted": contacted,
        "in_progress": in_progress,
        "confirmed": confirmed,
        "closed": closed
    }


def get_all_providers():
    """Get all unique providers who have interests"""
    providers = frappe.db.sql("""
        SELECT DISTINCT ci.provider, u.full_name
        FROM `tabCustomer Interest` ci
        LEFT JOIN `tabUser` u ON ci.provider = u.name
        WHERE ci.interest_type = 'OFFERING'
        ORDER BY u.full_name
    """, as_dict=True)
    return providers
