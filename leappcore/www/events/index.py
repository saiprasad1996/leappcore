import frappe
from urllib.parse import quote
from leappcore.backend.common.context import PageContext


def get_context(context):
    """Build page context for /events with filtering, pagination, and view toggling."""
    context = _init_page_context(context)

    page = max(int(frappe.form_dict.get("page", 1)), 1)
    per_page = 12
    search_query, area_filter, view_mode = _parse_filters()

    where_clause, params = _build_conditions(search_query, area_filter)
    start = (page - 1) * per_page

    events = _fetch_events(where_clause, params, start, per_page)
    _attach_detail_urls(events)

    context.events = events
    context.total_count = _count_events(where_clause, params)
    context.page = page
    context.per_page = per_page
    context.total_pages = (context.total_count + per_page - 1) // per_page
    context.view_mode = view_mode

    context.areas = _list_areas()

    context.search_query = search_query
    context.area_filter = area_filter
    context.filter_query = _build_filter_query(search_query, area_filter)
    return context


def _init_page_context(context):
    page_context = PageContext(context)
    context = page_context.get_context()
    context.csrf_token = frappe.sessions.get_csrf_token()
    return context


def _parse_filters():
    search_query = (frappe.form_dict.get("search") or "").strip()
    area_filter = _as_list("area")
    view_mode = frappe.form_dict.get("view", "gallery")
    return search_query, area_filter, view_mode


def _as_list(key):
    """Robustly get list-like values from form_dict even when getlist is missing."""
    getter = getattr(frappe.form_dict, "getlist", None)
    raw = getter(key) if callable(getter) else frappe.form_dict.get(key)
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [v for v in raw if v]
    return [raw] if raw else []


def _build_conditions(search_query, area_filter):
    conditions = ["e.active = 1"]
    params = {}

    if search_query:
        conditions.append("(e.event_name LIKE %(search_query)s OR e.short_description LIKE %(search_query)s OR e.long_description LIKE %(search_query)s)")
        params["search_query"] = f"%{search_query}%"

    if area_filter:
        conditions.append("e.area IN %(area_filter)s")
        params["area_filter"] = tuple(area_filter)

    where_clause = " AND ".join(conditions)
    return where_clause, params


def _fetch_events(where_clause, params, start, per_page):
    sql = f"""
        SELECT
            e.name,
            e.event_name,
            e.heading,
            e.organizer,
            e.area,
            e.start_datetime,
            e.end_datetime,
            e.short_description,
            e.long_description,
            e.venue_address,
            e.featured_image,
            e.active
        FROM `tabLeapp Event` e
        WHERE {where_clause}
        ORDER BY e.start_datetime DESC
        LIMIT %(start)s, %(limit)s
    """
    params["start"] = start
    params["limit"] = per_page
    return frappe.db.sql(sql, params, as_dict=True)


def _count_events(where_clause, params):
    sql = f"SELECT COUNT(*) FROM `tabLeapp Event` e WHERE {where_clause}"
    return frappe.db.sql(sql, params)[0][0]


def _attach_detail_urls(events):
    for event in events:
        event["detail_url"] = f"/events/detail?event={str(event.name)}"


def _list_areas():
    return frappe.get_all("Area", fields=["name", "area_name"], order_by="area_name")


def _build_filter_query(search_query, area_filter):
    parts = []
    if search_query:
        parts.append(f"search={quote(search_query)}")
    for area in area_filter:
        parts.append(f"area={quote(area)}")
    return "&".join(parts) if parts else ""
