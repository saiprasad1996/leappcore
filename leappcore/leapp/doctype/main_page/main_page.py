# Copyright (c) 2024, Leapp and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

MAX_HERO_SLIDES = 4
REQUIRED_SLIDE_FIELDS = ("headline", "subtext")


class MainPage(Document):
	def validate(self):
		validate_hero_slides(self.hero_slides)


def normalize_button_link(link):
	"""Strip whitespace; prefix / for relative paths without a scheme."""
	if link is None:
		return ""
	link = str(link).strip()
	if not link:
		return ""
	if "://" in link or link.startswith("/"):
		return link
	return f"/{link}"


def validate_hero_slides(hero_slides):
	"""Enforce max slides, required content fields, and normalized button links."""
	hero_slides = hero_slides or []
	if len(hero_slides) > MAX_HERO_SLIDES:
		frappe.throw(
			_("Hero carousel supports at most {0} slides. Remove extra rows before saving.").format(
				MAX_HERO_SLIDES
			)
		)

	for idx, slide in enumerate(hero_slides, start=1):
		image = (getattr(slide, "image", None) if not isinstance(slide, dict) else slide.get("image")) or ""
		if not str(image).strip():
			continue

		for fieldname in REQUIRED_SLIDE_FIELDS:
			value = (
				getattr(slide, fieldname, None)
				if not isinstance(slide, dict)
				else slide.get(fieldname)
			)
			if not str(value or "").strip():
				label = fieldname.replace("_", " ").title()
				frappe.throw(
					_("Hero slide {0}: {1} is required when an image is set.").format(idx, label)
				)

		if isinstance(slide, dict):
			slide["button_link"] = normalize_button_link(slide.get("button_link"))
		else:
			slide.button_link = normalize_button_link(slide.button_link)
