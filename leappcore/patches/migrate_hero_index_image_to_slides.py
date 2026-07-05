# Copyright (c) 2026, Leapp and contributors

import frappe


def execute():
	"""Copy legacy index_image into hero_slides when the carousel table is empty."""
	main_page = frappe.get_single("Main Page")
	if main_page.hero_slides or not main_page.index_image:
		return

	main_page.append(
		"hero_slides",
		{
			"image": main_page.index_image,
			"alt_text": "Hero slide",
			"sort_order": 1,
		},
	)
	main_page.save(ignore_permissions=True)
	frappe.db.commit()
