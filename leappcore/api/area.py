import frappe
from frappe import _


@frappe.whitelist(allow_guest=False)
def search_areas(query="", limit=20):
    """
    Search areas by name with pagination.
    Used for searchable dropdowns that may have 100s of areas.
    """
    filters = {}
    if query:
        filters["area_name"] = ["like", f"%{query}%"]
    
    areas = frappe.get_all(
        "Area",
        filters=filters,
        fields=["name", "area_name"],
        order_by="area_name",
        limit_page_length=int(limit)
    )
    
    return areas


@frappe.whitelist(allow_guest=False)
def get_area(area_name):
    """
    Get a single area by name.
    Used to load the selected area details.
    """
    if not area_name or not frappe.db.exists("Area", area_name):
        return None
    
    area = frappe.get_doc("Area", area_name)
    return {
        "name": area.name,
        "area_name": area.area_name
    }
