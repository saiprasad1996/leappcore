# Copyright (c) 2026, Sai Prasad and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from leappcore.leapp.doctype.main_page.main_page import (
	MAX_HERO_SLIDES,
	normalize_button_link,
	validate_hero_slides,
)

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


def _full_slide(i):
	return {
		"image": f"/files/hero-{i}.png",
		"headline": f"Headline {i}",
		"subtext": f"Subtext for slide {i}",
		"button_text": "Explore",
		"button_link": "/courses",
		"sort_order": i,
	}


class IntegrationTestMainPage(IntegrationTestCase):
	def test_validate_hero_slides_accepts_up_to_four(self):
		slides = [_full_slide(i) for i in range(1, MAX_HERO_SLIDES + 1)]
		validate_hero_slides(slides)

	def test_validate_hero_slides_rejects_more_than_four(self):
		slides = [_full_slide(i) for i in range(1, MAX_HERO_SLIDES + 2)]
		with self.assertRaises(frappe.ValidationError):
			validate_hero_slides(slides)

	def test_validate_hero_slides_requires_content_fields(self):
		slide = _full_slide(1)
		slide["headline"] = ""
		with self.assertRaises(frappe.ValidationError):
			validate_hero_slides([slide])

	def test_validate_hero_slides_allows_blank_button_fields(self):
		slide = _full_slide(1)
		slide["button_text"] = ""
		slide["button_link"] = ""
		validate_hero_slides([slide])

	def test_normalize_button_link(self):
		self.assertEqual(normalize_button_link("courses"), "/courses")
		self.assertEqual(normalize_button_link("/courses"), "/courses")
		self.assertEqual(normalize_button_link("https://example.com/x"), "https://example.com/x")
		self.assertEqual(normalize_button_link("  events  "), "/events")
		self.assertEqual(normalize_button_link(""), "")

	def test_validate_hero_slides_normalizes_button_link(self):
		slide = _full_slide(1)
		slide["button_link"] = "courses"
		validate_hero_slides([slide])
		self.assertEqual(slide["button_link"], "/courses")

	def test_main_page_save_rejects_fifth_hero_slide(self):
		main_page = frappe.get_single("Main Page")
		original_slides = [row.as_dict() for row in main_page.hero_slides]
		try:
			main_page.hero_slides = []
			for i in range(1, MAX_HERO_SLIDES + 2):
				main_page.append("hero_slides", _full_slide(i))
			with self.assertRaises(frappe.ValidationError):
				main_page.save(ignore_permissions=True)
		finally:
			main_page.hero_slides = []
			for row in original_slides:
				main_page.append("hero_slides", row)
			main_page.save(ignore_permissions=True)
