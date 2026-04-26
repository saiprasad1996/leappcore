import frappe
from urllib.parse import quote
from leappcore.backend.common.context import PageContext
from leappcore.backend.common.event_cards import enrich_events_for_cards


def get_context(context):
    """Build page context for /events with filtering, pagination, and view toggling."""
    context = _init_page_context(context)

    page = max(int(frappe.form_dict.get("page", 1)), 1)
    per_page = 12
    search_query, location_filter, area_filter_raw, view_mode = _parse_filters()

    areas = _list_areas(location_filter)
    valid_area_names = {a["name"] for a in areas}
    area_filter = [a for a in area_filter_raw if a in valid_area_names]

    where_clause, params = _build_conditions(search_query, location_filter, area_filter)
    start = (page - 1) * per_page

    events = _fetch_events(where_clause, params, start, per_page)
    enrich_events_for_cards(events)
    _attach_detail_urls(events)

    context.events = events
    context.total_count = _count_events(where_clause, params)
    context.page = page
    context.per_page = per_page
    context.total_pages = (context.total_count + per_page - 1) // per_page
    context.view_mode = view_mode

    context.locations = _list_locations()
    context.areas = areas

    context.search_query = search_query
    context.location_filter = location_filter
    context.area_filter = area_filter
    context.filter_query = _build_filter_query(search_query, location_filter, area_filter)
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
    location_filter = (frappe.form_dict.get("location") or "").strip()
    area_filter = _as_list("area")
    view_mode = frappe.form_dict.get("view", "gallery")
    return search_query, location_filter, area_filter, view_mode


def _as_list(key):
    """Robustly get list-like values from form_dict even when getlist is missing."""
    getter = getattr(frappe.form_dict, "getlist", None)
    raw = getter(key) if callable(getter) else frappe.form_dict.get(key)
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [v for v in raw if v]
    return [raw] if raw else []


def _build_conditions(search_query, location_filter, area_filter):
    conditions = ["e.active = 1"]
    params = {}

    if search_query:
        conditions.append(
            "(e.event_name LIKE %(search_query)s OR e.short_description LIKE %(search_query)s OR e.long_description LIKE %(search_query)s)"
        )
        params["search_query"] = f"%{search_query}%"

    if location_filter:
        conditions.append("e.location = %(location_filter)s")
        params["location_filter"] = location_filter

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
            e.organizer,
            e.area,
            e.location,
            e.start_datetime,
            e.end_datetime,
            e.short_description,
            e.venue_address,
            e.featured_image,
            e.active,
            COALESCE(loc.city, loc_from_area.city) AS city,
            a.area_name AS area_name
        FROM `tabLeapp Event` e
        LEFT JOIN `tabLocation` loc ON loc.name = e.location
        LEFT JOIN `tabArea` a ON a.name = e.area
        LEFT JOIN `tabLocation` loc_from_area ON loc_from_area.name = a.location
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


def _list_locations():
    return frappe.get_all("Location", fields=["name", "city"], order_by="city asc")


def _list_areas(location_name=None):
    filters = {}
    if location_name:
        filters["location"] = location_name
    return frappe.get_all(
        "Area",
        filters=filters,
        fields=["name", "area_name"],
        order_by="area_name",
    )


def _build_filter_query(search_query, location_filter, area_filter):
    parts = []
    if search_query:
        parts.append(f"search={quote(search_query)}")
    if location_filter:
        parts.append(f"location={quote(location_filter)}")
    for area in area_filter:
        parts.append(f"area={quote(area)}")
    return "&".join(parts) if parts else ""
