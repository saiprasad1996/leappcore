# Copyright (c) 2024, Leapp and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

MAX_HERO_SLIDES = 4


class MainPage(Document):
	def validate(self):
		validate_hero_slides(self.hero_slides)


def validate_hero_slides(hero_slides):
	"""Reject more than MAX_HERO_SLIDES rows in the hero carousel."""
	if len(hero_slides or []) > MAX_HERO_SLIDES:
		frappe.throw(
			_("Hero carousel supports at most {0} slides. Remove extra rows before saving.").format(
				MAX_HERO_SLIDES
			)
		)
