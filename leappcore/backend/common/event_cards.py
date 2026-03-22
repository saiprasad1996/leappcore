"""Shared helpers for event cards on listing pages."""

import frappe


def enrich_events_for_cards(events: list) -> None:
    """Mutate each event dict with `categories` (Offering Category display names)."""
    if not events:
        return

    names = [str(e["name"]) for e in events]

    cat_rows = frappe.get_all(
        "Leapp Event Category Table",
        filters={"parent": ["in", names]},
        fields=["parent", "event_category"],
        order_by="idx asc",
    )
    cat_ids = list(
        {r["event_category"] for r in cat_rows if r.get("event_category")}
    )
    cat_id_to_label = {}
    if cat_ids:
        for row in frappe.get_all(
            "Offering Category",
            filters={"name": ["in", cat_ids]},
            fields=["name", "category_name"],
        ):
            cat_id_to_label[row["name"]] = row["category_name"] or row["name"]

    cats_by_parent: dict[str, list] = {}
    for r in cat_rows:
        oc = r.get("event_category")
        label = cat_id_to_label.get(oc, oc) if oc else None
        if not label:
            continue
        pid = str(r.get("parent") or "")
        lst = cats_by_parent.setdefault(pid, [])
        if label not in lst:
            lst.append(label)

    for e in events:
        e["categories"] = cats_by_parent.get(str(e["name"]), [])
