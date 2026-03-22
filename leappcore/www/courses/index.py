import frappe
from urllib.parse import quote
from leappcore.backend.common.context import PageContext
from leappcore.backend.common.offering_cards import enrich_offerings_for_cards


def get_context(context):
    """Build page context for /courses with filtering, pagination, and view toggling."""
    context = _init_page_context(context)

    page = max(int(frappe.form_dict.get("page", 1)), 1)
    per_page = 12
    search_query, category_filter, location_filter, group_filter, view_mode = _parse_filters()

    where_clause, params = _build_conditions(search_query, category_filter, location_filter, group_filter)
    start = (page - 1) * per_page

    offerings = _fetch_offerings(where_clause, params, start, per_page)
    enrich_offerings_for_cards(offerings)
    _attach_detail_urls(offerings)

    context.offerings = offerings
    context.total_count = _count_offerings(where_clause, params)
    context.page = page
    context.per_page = per_page
    context.total_pages = (context.total_count + per_page - 1) // per_page
    context.view_mode = view_mode

    context.categories = _list_categories(group_filter)
    context.locations = _list_locations()

    context.search_query = search_query
    context.category_filter = category_filter
    context.location_filter = location_filter
    context.group_filter = group_filter
    context.filter_query = _build_filter_query(search_query, category_filter, location_filter, group_filter)
    return context


def _init_page_context(context):
    page_context = PageContext(context)
    context = page_context.get_context()
    context.csrf_token = frappe.sessions.get_csrf_token()
    # Prevent caching since page contains user-specific navigation
    context.no_cache = 1
    return context


def _parse_filters():
    search_query = (frappe.form_dict.get("search") or "").strip()
    category_filter = _as_list("category")
    location_filter = _as_list("location")
    group_filter = (frappe.form_dict.get("group") or "").strip()
    view_mode = frappe.form_dict.get("view", "gallery")
    return search_query, category_filter, location_filter, group_filter, view_mode


def _as_list(key):
    """Robustly get list-like values from form_dict even when getlist is missing."""
    getter = getattr(frappe.form_dict, "getlist", None)
    raw = getter(key) if callable(getter) else frappe.form_dict.get(key)
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [v for v in raw if v]
    return [raw] if raw else []


def _build_conditions(search_query, category_filter, location_filter, group_filter):
    conditions = ["o.active = 1"]
    params = {}

    if search_query:
        conditions.append("(o.title LIKE %(search_query)s OR o.description LIKE %(search_query)s)")
        params["search_query"] = f"%{search_query}%"

    if category_filter:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM `tabOffering Category Table` oct
                WHERE oct.parent = o.name AND oct.offering_category IN %(category_filter)s
            )
        """)
        params["category_filter"] = tuple(category_filter)

    if location_filter:
        conditions.append("""
            EXISTS (
                SELECT 1
                FROM `tabOffering Area Table` oat
                JOIN `tabArea` area ON area.name = oat.area
                JOIN `tabLocation` loc ON loc.name = area.location
                WHERE oat.parent = o.name AND loc.city IN %(location_filter)s
            )
        """)
        params["location_filter"] = tuple(location_filter)

    if group_filter:
        conditions.append("""
            EXISTS (
                SELECT 1
                FROM `tabOffering Category Table` oct
                JOIN `tabOffering Category` oc ON oc.name = oct.offering_category
                WHERE oct.parent = o.name AND oc.parent_group = %(group_filter)s
            )
        """)
        params["group_filter"] = group_filter

    return " AND ".join(conditions), params


def _fetch_offerings(where_clause, params, start, per_page):
    return frappe.db.sql(f"""
        SELECT DISTINCT
            o.name, o.title, o.subtitle, o.description, o.image, o.duration_hours, o.level,
            o.price, o.negotiable
        FROM `tabOffering` o
        WHERE {where_clause}
        ORDER BY o.modified DESC
        LIMIT %(start)s, %(per_page)s
    """, {**params, "start": start, "per_page": per_page}, as_dict=True)


def _attach_detail_urls(offerings):
    for offering in offerings:
        offering["detail_url"] = f"/courses/detail?offering={str(offering['name'])}"


def _count_offerings(where_clause, params):
    return frappe.db.sql(f"""
        SELECT COUNT(DISTINCT o.name) AS total
        FROM `tabOffering` o
        WHERE {where_clause}
    """, params, as_dict=True)[0].total


def _list_categories(group_filter=None):
    filters = {}
    if group_filter:
        filters["parent_group"] = group_filter
    
    return frappe.get_all(
        "Offering Category",
        filters=filters,
        fields=["name", "category_name", "parent_group"],
        order_by="parent_group, category_name",
    )


def _list_locations():
    return frappe.get_all(
        "Location",
        fields=["city"],
        order_by="city",
    )


def _build_filter_query(search_query, category_filter, location_filter, group_filter):
    def _encode_list(params, key):
        return "".join([f"&{key}={quote(str(val))}" for val in params])

    filter_query = ""
    if search_query:
        filter_query += f"&search={quote(search_query)}"
    filter_query += _encode_list(category_filter, "category")
    filter_query += _encode_list(location_filter, "location")
    if group_filter:
        filter_query += f"&group={quote(group_filter)}"
    return filter_query
