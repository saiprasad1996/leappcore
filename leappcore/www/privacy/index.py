import frappe


def get_context(context):
    """Render Privacy Policy page"""
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Get content from Main Page doctype
    main_page = frappe.get_single("Main Page")
    context.privacy_content = main_page.privacy_policy or ""
    context.page_title = "Privacy Policy"
