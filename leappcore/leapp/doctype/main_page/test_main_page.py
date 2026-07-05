# Copyright (c) 2026, Sai Prasad and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from leappcore.leapp.doctype.main_page.main_page import MAX_HERO_SLIDES, validate_hero_slides

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


class IntegrationTestMainPage(IntegrationTestCase):
	def test_validate_hero_slides_accepts_up_to_four(self):
		slides = [{"image": f"/files/hero-{i}.png", "sort_order": i} for i in range(1, MAX_HERO_SLIDES + 1)]
		validate_hero_slides(slides)

	def test_validate_hero_slides_rejects_more_than_four(self):
		slides = [{"image": f"/files/hero-{i}.png", "sort_order": i} for i in range(1, MAX_HERO_SLIDES + 2)]
		with self.assertRaises(frappe.ValidationError):
			validate_hero_slides(slides)

	def test_main_page_save_rejects_fifth_hero_slide(self):
		main_page = frappe.get_single("Main Page")
		original_slides = [row.as_dict() for row in main_page.hero_slides]
		try:
			main_page.hero_slides = []
			for i in range(1, MAX_HERO_SLIDES + 2):
				main_page.append(
					"hero_slides",
					{"image": f"/files/test-hero-{i}.png", "sort_order": i},
				)
			with self.assertRaises(frappe.ValidationError):
				main_page.save(ignore_permissions=True)
		finally:
			main_page.hero_slides = []
			for row in original_slides:
				main_page.append("hero_slides", row)
			main_page.save(ignore_permissions=True)
