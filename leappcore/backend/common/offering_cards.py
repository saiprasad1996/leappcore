"""Shared helpers for course/offering cards on listing and home pages."""

import frappe


def enrich_offerings_for_cards(offerings: list) -> None:
    """Mutate each offering dict with `categories` (display names) and `locations` (city/area rows)."""
    if not offerings:
        return

    # Normalize to str so SQL rows (int/str autoincrement) match child table `parent` values
    names = [str(o["name"]) for o in offerings]

    cat_rows = frappe.get_all(
        "Offering Category Table",
        filters={"parent": ["in", names]},
        fields=["parent", "offering_category"],
        order_by="idx asc",
    )
    cat_ids = list(
        {r["offering_category"] for r in cat_rows if r.get("offering_category")}
    )
    cat_id_to_label = {}
    if cat_ids:
        for row in frappe.get_all(
            "Offering Category",
            filters={"name": ["in", cat_ids]},
            fields=["name", "category_name"],
        ):
            cat_id_to_label[row["name"]] = row["category_name"] or row["name"]

    area_rows = frappe.get_all(
        "Offering Area Table",
        filters={"parent": ["in", names]},
        fields=["parent", "location", "area"],
        order_by="idx asc",
    )
    loc_ids = list({r.get("location") for r in area_rows if r.get("location")})
    area_ids = list({r.get("area") for r in area_rows if r.get("area")})

    loc_city = {}
    if loc_ids:
        for row in frappe.get_all(
            "Location",
            filters={"name": ["in", loc_ids]},
            fields=["name", "city"],
        ):
            loc_city[row["name"]] = row.get("city") or ""

    area_names = {}
    if area_ids:
        for row in frappe.get_all(
            "Area",
            filters={"name": ["in", area_ids]},
            fields=["name", "area_name"],
        ):
            area_names[row["name"]] = row.get("area_name") or ""

    cats_by_parent: dict[str, list] = {}
    for r in cat_rows:
        oc = r.get("offering_category")
        label = cat_id_to_label.get(oc, oc) if oc else None
        if not label:
            continue
        pid = str(r.get("parent") or "")
        lst = cats_by_parent.setdefault(pid, [])
        if label not in lst:
            lst.append(label)

    locs_by_parent: dict[str, list] = {}
    seen_loc: dict[str, set] = {}
    for r in area_rows:
        city = loc_city.get(r.get("location"), "")
        area = area_names.get(r.get("area"), "")
        if not city and not area:
            continue
        key = (city, area)
        pid = str(r.get("parent") or "")
        s = seen_loc.setdefault(pid, set())
        if key in s:
            continue
        s.add(key)
        locs_by_parent.setdefault(pid, []).append({"city": city, "area": area})

    for o in offerings:
        key = str(o["name"])
        o["categories"] = cats_by_parent.get(key, [])
        o["locations"] = locs_by_parent.get(key, [])
