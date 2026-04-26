import frappe
from frappe import _
import json


def get_context(context):
    """Render offering registration page"""
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/partner/offering/register"
        raise frappe.Redirect
    
    # Check if user has Leapp Partner role
    if not has_partner_role():
        # Redirect customers to courses page
        frappe.local.flags.redirect_location = "/courses"
        raise frappe.Redirect
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Get offering ID if editing
    offering_id = frappe.form_dict.get("id")
    
    # Handle form submission
    if frappe.request.method == "POST":
        try:
            offering_id = save_offering(offering_id)
            frappe.local.flags.redirect_location = f"/partner/offering/register?id={offering_id}&success=1"
            raise frappe.Redirect
        except frappe.Redirect:
            raise
        except Exception as e:
            frappe.clear_messages()
            context.error_message = str(e)
            frappe.log_error(frappe.get_traceback(), "Offering Save Error")
    
    # Load offering if editing
    if offering_id:
        context.offering = load_offering(offering_id)
        context.is_edit = True
    else:
        context.offering = get_empty_offering()
        context.is_edit = False
    
    # Check for success message
    if frappe.form_dict.get("success"):
        context.success_message = _("Offering saved successfully!")
    
    # Load dropdown/select options
    context.my_offerings = get_my_offerings()
    context.categories = get_categories()
    context.category_parent_groups = get_category_parent_groups()
    context.locations = get_locations()
    context.areas = get_areas()
    context.languages = get_languages()
    context.skill_levels = get_skill_levels()
    
    return context


def has_partner_role():
    """Check if current user has Leapp Partner role"""
    return "Leapp Partner" in frappe.get_roles(frappe.session.user)


def get_empty_offering():
    """Return empty offering structure"""
    return {
        "title": "",
        "subtitle": "",
        "description": "",
        "image": "",
        "price": 0,
        "duration_hours": 0,
        "levels": [],
        "languages": [],
        "total_sessions": 0,
        "active": 0,
        "featured": 0,
        "address": "",
        "categories": [],
        "category_parent": "",
        "location": "",
        "location_display": "",
        "areas": [],
        "highlights": [],
        "program_outline": [],
        "prices": [],
        "schedules": [],
        "instructors": [],
        "instructor_details": [],
    }


def load_offering(offering_id):
    """Load offering for editing"""
    if not frappe.db.exists("Offering", offering_id):
        frappe.throw(_("Offering not found"))
    
    offering = frappe.get_doc("Offering", offering_id)
    
    # Check if current user is the provider
    if offering.provider != frappe.session.user:
        frappe.throw(_("You do not have permission to edit this offering"), frappe.PermissionError)
    
    data = offering.as_dict()
    
    # Convert child tables to proper format (only include needed fields, convert time to string)
    data["categories"] = [row.offering_category for row in offering.categories]
    data["areas"] = [row.area for row in offering.areas]
    data["location"] = ""
    data["location_display"] = ""
    for row in offering.areas or []:
        loc = frappe.db.get_value("Area", row.area, "location")
        if loc:
            data["location"] = loc
            data["location_display"] = frappe.db.get_value("Location", loc, "city") or loc
            break
    data["instructors"] = [row.instructor for row in offering.instructors]
    data["instructor_details"] = []
    for uid in data["instructors"]:
        if not uid:
            continue
        data["instructor_details"].append(
            {
                "name": uid,
                "full_name": frappe.db.get_value("User", uid, "full_name") or uid,
                "email": frappe.db.get_value("User", uid, "email") or "",
            }
        )
    data["languages"] = [row.language for row in (offering.language or [])]
    data["address"] = offering.address or ""
    data["levels"] = [row.skill for row in (offering.level or [])]
    
    data["highlights"] = [{
        "order_no": row.order_no or 0,
        "icon": row.icon or "kid_star",
        "label": row.label or "",
        "value": row.value or ""
    } for row in offering.highlights]
    
    data["program_outline"] = [{
        "order_no": row.order_no or 0,
        "title": row.title or "",
        "description": row.description or "",
        "duration": row.duration or 0
    } for row in offering.program_outline]
    
    data["prices"] = [{
        "amount": float(row.amount or 0),
        "currency": row.currency or "INR",
        "billing_type": row.billing_type or "per_session"
    } for row in offering.prices]
    
    data["schedules"] = [{
        "recurrence": row.recurrence or "Once",
        "start_time": str(row.start_time) if row.start_time else "",
        "end_time": str(row.end_time) if row.end_time else "",
        "days_of_week": row.days_of_week or ""
    } for row in offering.schedules]

    data["category_parent"] = infer_category_parent_group(data["categories"])
    
    return data


def get_my_offerings():
    """Get all offerings created by current user"""
    offerings = frappe.get_all(
        "Offering",
        filters={"provider": frappe.session.user},
        fields=["name", "title", "subtitle", "price", "active", "featured", "modified"],
        order_by="modified desc"
    )
    return offerings


def get_categories():
    """Get all offering categories"""
    categories = frappe.get_all(
        "Offering Category",
        fields=["name", "category_name", "parent_group"],
        order_by="parent_group, category_name"
    )
    return categories


def get_category_parent_groups():
    """Distinct parent_group values for the Category (parent) dropdown."""
    rows = frappe.get_all(
        "Offering Category",
        fields=["parent_group"],
        filters={"parent_group": ("!=", "")},
        distinct=True,
        order_by="parent_group asc",
    )
    groups = [r.parent_group for r in rows if r.get("parent_group")]
    preferred = ["Learn", "Leisure", "Play"]
    ordered = [g for g in preferred if g in groups]
    for g in groups:
        if g not in ordered:
            ordered.append(g)
    return ordered


def infer_category_parent_group(category_names):
    """Pick parent group for edit form when subcategories may span groups (use majority)."""
    if not category_names:
        return ""
    counts = {}
    for cn in category_names:
        pg = frappe.db.get_value("Offering Category", cn, "parent_group")
        if pg:
            counts[pg] = counts.get(pg, 0) + 1
    if not counts:
        return ""
    return max(counts.items(), key=lambda x: (x[1], x[0]))[0]


def get_locations():
    """Cities / locations for filtering areas."""
    return frappe.get_all(
        "Location",
        fields=["name", "city"],
        order_by="city asc",
    )


def get_areas():
    """All areas with parent Location (for client-side filtering)."""
    return frappe.get_all(
        "Area",
        fields=["name", "area_name", "location"],
        order_by="area_name asc",
    )


def get_languages():
    """Languages selectable on offerings (must match Link target on Offering languages)."""
    return frappe.get_all(
        "Leapp Languages",
        fields=["name", "language", "symbol"],
        order_by="language",
    )

def get_skill_levels():
    """Get all skill levels from the Offering skills doctype"""
    return frappe.get_all(
        "Offering skills",
        fields=["name", "skill"],
        order_by="skill"
    )



def _validate_instructor_user(user_id: str) -> None:
    if not user_id or not frappe.db.exists("User", user_id):
        frappe.throw(_("Invalid instructor."))
    if not frappe.db.get_value("User", user_id, "enabled"):
        frappe.throw(_("Instructor account is disabled."))
    if "Leapp Partner" not in frappe.get_roles(user_id):
        frappe.throw(_("Instructor must be a Leapp Partner."))


def save_offering(offering_id=None):
    """Save offering with all fields"""
    user = frappe.session.user
    
    # Get form data
    title = frappe.form_dict.get("title")
    subtitle = frappe.form_dict.get("subtitle")
    description = frappe.form_dict.get("description")
    price = frappe.form_dict.get("price", 0)
    duration_hours = frappe.form_dict.get("duration_hours", 0)
    levels = json.loads(frappe.form_dict.get("levels") or "[]")
    if not isinstance(levels, list):
        levels = []
    languages = json.loads(frappe.form_dict.get("languages") or "[]")
    if not isinstance(languages, list):
        languages = []
    address = frappe.form_dict.get("address", "")
    total_sessions = frappe.form_dict.get("total_sessions", 0)
    active = 1 if frappe.form_dict.get("active") else 0
    featured = 1 if frappe.form_dict.get("featured") else 0
    
    # Get child table data (JSON strings)
    categories = json.loads(frappe.form_dict.get("categories") or "[]")
    areas = json.loads(frappe.form_dict.get("areas") or "[]")
    instructors = json.loads(frappe.form_dict.get("instructors") or "[]")
    highlights = json.loads(frappe.form_dict.get("highlights") or "[]")
    program_outline = json.loads(frappe.form_dict.get("program_outline") or "[]")
    prices = json.loads(frappe.form_dict.get("prices") or "[]")
    schedules = json.loads(frappe.form_dict.get("schedules") or "[]")
    for name, seq in (
        ("categories", categories),
        ("areas", areas),
        ("instructors", instructors),
        ("highlights", highlights),
        ("program_outline", program_outline),
        ("prices", prices),
        ("schedules", schedules),
    ):
        if not isinstance(seq, list):
            frappe.throw(_("Invalid {0} data").format(name))

    # Validate required fields
    if not title:
        frappe.throw(_("Title is required"))
    
    if offering_id:
        # Update existing offering
        offering = frappe.get_doc("Offering", offering_id)
        
        # Check permission
        if offering.provider != user:
            frappe.throw(_("You do not have permission to edit this offering"), frappe.PermissionError)
        
        offering.title = title
        offering.subtitle = subtitle
        offering.description = description
        offering.price = price
        offering.duration_hours = duration_hours
        offering.total_sessions = total_sessions
        offering.active = active
        offering.featured = featured
        offering.address = address
        
        # Clear and rebuild child tables
        offering.categories = []
        offering.areas = []
        offering.instructors = []
        offering.level = []
        offering.language = []
        offering.highlights = []
        offering.program_outline = []
        offering.prices = []
        offering.schedules = []
        
    else:
        # Create new offering
        offering = frappe.get_doc({
            "doctype": "Offering",
            "provider": user,
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "price": price,
            "duration_hours": duration_hours,
            "address": address,
            "total_sessions": total_sessions,
            "active": active,
            "featured": featured
        })
    
    # Add child table rows
    for cat in categories:
        if cat:
            offering.append("categories", {"offering_category": cat})
    
    for area in areas:
        if area:
            offering.append("areas", {"area": area})
    
    for inst in instructors:
        if inst:
            _validate_instructor_user(inst)
            offering.append("instructors", {"instructor": inst})

    for lang in languages:
        if lang:
            offering.append("language", {"language": lang})

    for lvl in levels:
        if lvl:
            offering.append("level", {"skill": lvl})
    
    for h in highlights:
        if not isinstance(h, dict):
            continue
        if h.get("label") or h.get("value"):
            offering.append("highlights", {
                "order_no": h.get("order_no", 0),
                "icon": h.get("icon", "kid_star"),
                "label": h.get("label", ""),
                "value": h.get("value", "")
            })
    
    for p in program_outline:
        if not isinstance(p, dict):
            continue
        if p.get("title"):
            offering.append("program_outline", {
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "duration": p.get("duration", 0),
                "order_no": p.get("order_no", 0)
            })
    
    for pr in prices:
        if not isinstance(pr, dict):
            continue
        if pr.get("amount"):
            offering.append("prices", {
                "amount": pr.get("amount", 0),
                "currency": pr.get("currency", "INR"),
                "billing_type": pr.get("billing_type", "per_session")
            })
    
    for s in schedules:
        if not isinstance(s, dict):
            continue
        if s.get("recurrence"):
            offering.append("schedules", {
                "recurrence": s.get("recurrence", "Once"),
                "start_time": s.get("start_time"),
                "end_time": s.get("end_time"),
                "days_of_week": s.get("days_of_week", "")
            })
    
    if offering_id:
        offering.save(ignore_permissions=True)
    else:
        offering.insert(ignore_permissions=True)

    if frappe.request.files.get("image"):
        file = frappe.request.files.get("image")
        if file.filename:
            from frappe.utils.file_manager import save_file

            saved_file = save_file(
                file.filename,
                file.read(),
                "Offering",
                offering.name,
                folder="Home/Attachments",
                is_private=0,
            )
            offering.image = saved_file.file_url
            offering.save(ignore_permissions=True)

    frappe.db.commit()
    return offering.name
