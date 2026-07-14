# Copyright (c) 2026, Leapp and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class PartnerVerificationTemplate(Document):
	def validate(self):
		seen = set()
		for row in self.fields or []:
			key = (row.field_key or "").strip().lower()
			if not key:
				frappe.throw(frappe._("Field Key is required on every template field row."))
			if not re.match(r"^[a-z][a-z0-9_]*$", key):
				frappe.throw(
					frappe._(
						"Field Key '{0}' must be snake_case starting with a letter."
					).format(row.field_key)
				)
			row.field_key = key
			if key in seen:
				frappe.throw(frappe._("Duplicate Field Key: {0}").format(key))
			seen.add(key)
