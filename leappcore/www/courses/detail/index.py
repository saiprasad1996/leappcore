import frappe
from frappe.exceptions import DoesNotExistError
from leappcore.backend.common.context import PageContext


def get_context(context):
    """Render offering detail with live data."""
    context = PageContext(context).get_context()
    context.csrf_token = frappe.sessions.get_csrf_token()

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


def _load_offering(offering_id: str):
    doc = frappe.get_doc("Offering", offering_id)

    placeholder_image = "https://placehold.co/800x500?text=No+Image"
    description_paragraphs = (doc.description or "").split("\n\n")
    description_paragraphs = [p.strip() for p in description_paragraphs if p.strip()]

    highlights = frappe.get_all(
        "Offering Highlight",
        filters={"parent": doc.name},
        fields=["icon", "label", "value", "order_no"],
        order_by="COALESCE(order_no, 1000), creation",
    )
    if not highlights:
        highlights = _default_highlights(doc)

    program_outline = frappe.get_all(
        "Offering Program Outline",
        filters={"parent": doc.name},
        fields=["title", "description", "duration", "order_no"],
        order_by="COALESCE(order_no, 1000), creation",
    )

    instructors = []
    for row in doc.get("instructors") or []:
        full_name = frappe.db.get_value("User", row.instructor, "full_name") or row.instructor
        avatar = frappe.db.get_value("User", row.instructor, "user_image") or placeholder_image
        instructors.append(
            {
                "name": full_name,
                "avatar": avatar,
                "profile_url": f"/app/user/{row.instructor}",
            }
        )

    return {
        "name": doc.name,
        "title": doc.title,
        "subtitle": doc.subtitle,
        "description": description_paragraphs,
        "image": doc.image or placeholder_image,
        "price": doc.price or 0,
        "duration_hours": doc.duration_hours,
        "level": doc.level,
        "total_sessions": doc.total_sessions,
        "highlights": highlights,
        "instructors": instructors,
        "program_outline": program_outline,
    }


def _default_highlights(doc):
    parts = []
    if doc.duration_hours:
        parts.append({"icon": "schedule", "label": "Duration", "value": f"{doc.duration_hours} hours"})
    if doc.level:
        parts.append({"icon": "bar_chart", "label": "Level", "value": doc.level})
    if doc.total_sessions:
        parts.append({"icon": "list_alt", "label": "Sessions", "value": f"{doc.total_sessions} Sessions"})
    return parts
