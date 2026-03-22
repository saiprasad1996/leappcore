import frappe
from urllib.parse import quote
from leappcore.backend.common.context import PageContext


def get_context(context):
    context = PageContext(context).get_context()
    context.no_cache = 1

    page = max(int(frappe.form_dict.get("page", 1)), 1)
    per_page = 12
    search_query = (frappe.form_dict.get("search") or "").strip()
    view_mode = frappe.form_dict.get("view", "gallery")

    where_clause, params = _build_conditions(search_query)
    start = (page - 1) * per_page

    blogs = _fetch_blogs(where_clause, params, start, per_page)
    total_count = _count_blogs(where_clause, params)

    context.blogs = blogs
    context.total_count = total_count
    context.page = page
    context.per_page = per_page
    context.total_pages = (total_count + per_page - 1) // per_page
    context.view_mode = view_mode
    context.search_query = search_query
    context.filter_query = _build_filter_query(search_query)

    return context


def _build_conditions(search_query):
    conditions = ["published = 1"]
    params = {}
    if search_query:
        conditions.append("(title LIKE %(search)s OR author LIKE %(search)s)")
        params["search"] = f"%{search_query}%"
    return " AND ".join(conditions), params


def _fetch_blogs(where_clause, params, start, per_page):
    sql = f"""
        SELECT name, title, image, author, creation
        FROM `tabNewsBlogs`
        WHERE {where_clause}
        ORDER BY creation DESC
        LIMIT %(start)s, %(limit)s
    """
    params["start"] = start
    params["limit"] = per_page
    return frappe.db.sql(sql, params, as_dict=True)


def _count_blogs(where_clause, params):
    count_params = {k: v for k, v in params.items() if k not in ("start", "limit")}
    return frappe.db.sql(f"SELECT COUNT(*) FROM `tabNewsBlogs` WHERE {where_clause}", count_params)[0][0]


def _build_filter_query(search_query):
    parts = []
    if search_query:
        parts.append(f"search={quote(search_query)}")
    return "&".join(parts) if parts else ""
