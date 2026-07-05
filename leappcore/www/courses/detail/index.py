import frappe
from urllib.parse import quote
from frappe.exceptions import DoesNotExistError
from leappcore.backend.common.context import PageContext


def get_context(context):
    """Render offering detail with live data."""
    context = PageContext(context).get_context()
    context.csrf_token = frappe.sessions.get_csrf_token()
    
    # Check if user has Leapp Customer role
    context.has_leapp_customer_role = False
    if frappe.session.user != "Guest":
        user_roles = frappe.get_roles(frappe.session.user)
        context.has_leapp_customer_role = "Leapp Customer" in user_roles
        if frappe.session.user == "Administrator":
            context.has_leapp_customer_role = False

    offering_id = frappe.form_dict.get("offering")
    if not offering_id:
        frappe.throw("Missing offering id in query string.")

    try:
        context.offering = _load_offering(offering_id)
    except DoesNotExistError:
        # Course not found - render the 404 page
        context.show_404 = True
        context.not_found_type = "course"
        context.offering_id = offering_id
        frappe.response["http_status_code"] = 404
    
    return context


def _area_chip_label(area_row_id: str) -> str:
    """Chip text: city + area from Area → Location (e.g. 'Bengaluru, Koramangala')."""
    if not area_row_id:
        return ""
    area_name = frappe.db.get_value("Area", area_row_id, "area_name") or area_row_id
    location = frappe.db.get_value("Area", area_row_id, "location")
    city = frappe.db.get_value("Location", location, "city") if location else None
    if city:
        return f"{city}, {area_name}"
    return area_name


def _load_offering(offering_id: str):
    doc = frappe.get_doc("Offering", offering_id)

    placeholder_image = "https://placehold.co/800x500?text=No+Image"
    description_paragraphs = (doc.description or "").split("\n\n")
    description_paragraphs = [p.strip() for p in description_paragraphs if p.strip()]

    # Always include core highlights (Duration, Level, Language, Sessions) first
    highlights = _default_highlights(doc)
    
    # Add any custom highlights after the defaults
    custom_highlights = frappe.get_all(
        "Offering Highlight",
        filters={"parent": doc.name},
        fields=["icon", "label", "value", "order_no"],
        order_by="order_no asc, creation asc",
    )
    highlights.extend(custom_highlights)

    program_outline = frappe.get_all(
        "Offering Program Outline",
        filters={"parent": doc.name},
        fields=["title", "description", "duration", "order_no"],
        order_by="order_no asc, creation asc",
    )

    instructors = []
    for row in doc.get("instructors") or []:
        full_name = frappe.db.get_value("User", row.instructor, "full_name") or row.instructor
        avatar = frappe.db.get_value("User", row.instructor, "user_image") or placeholder_image
        instructors.append(
            {
                "name": full_name,
                "avatar": avatar,
                "profile_url": f"/partner/profile/public?partner_id={quote(row.instructor, safe='')}",
            }
        )

    # Fetch languages from Table MultiSelect child rows
    languages = []
    for row in doc.get("language") or []:
        lang_name = frappe.db.get_value("Leapp Languages", row.language, "language") or row.language
        if lang_name:
            languages.append(lang_name)

    # Fetch areas (chip = city + area when Location is set on Area)
    areas = []
    for row in doc.get("areas") or []:
        label = _area_chip_label(row.area)
        if label:
            areas.append(label)

    # Fetch categories
    categories = []
    for row in doc.get("categories") or []:
        category_name = frappe.db.get_value("Offering Category", row.offering_category, "category_name") or row.offering_category
        categories.append(category_name)

    packages = frappe.get_all(
        "Offering Price",
        filters={"parent": doc.name},
        fields=["package_name", "amount", "currency", "billing_type"],
        order_by="idx asc",
    )

    return {
        "name": doc.name,
        "title": doc.title,
        "subtitle": doc.subtitle,
        "description": description_paragraphs,
        "image": doc.image or placeholder_image,
        "price": doc.price or 0,
        "negotiable": bool(doc.negotiable),
        "duration_hours": doc.duration_hours,
        "levels": [row.skill for row in (doc.get("level") or [])],
        "languages": languages,
        "total_sessions": doc.total_sessions,
        "highlights": highlights,
        "instructors": instructors,
        "program_outline": program_outline,
        "areas": areas,
        "categories": categories,
        "address": doc.address or "",
        "packages": packages,
        "share_url": frappe.utils.get_url(f"/courses/detail?offering={doc.name}"),
    }


def _default_highlights(doc):
    parts = []
    if doc.duration_hours:
        parts.append({"icon": "schedule", "label": "Duration", "value": f"{doc.duration_hours} hours"})
    level_names = [row.skill for row in (doc.get("level") or [])]
    if level_names:
        parts.append({"icon": "bar_chart", "label": "Level", "value": ", ".join(level_names)})
    lang_names = []
    for row in (doc.get("language") or []):
        lang_name = frappe.db.get_value("Leapp Languages", row.language, "language") or row.language
        if lang_name:
            lang_names.append(lang_name)
    if lang_names:
        parts.append({"icon": "translate", "label": "Language", "value": ", ".join(lang_names)})
    if doc.total_sessions:
        parts.append({"icon": "list_alt", "label": "Sessions", "value": f"{doc.total_sessions} Sessions"})
    return parts
