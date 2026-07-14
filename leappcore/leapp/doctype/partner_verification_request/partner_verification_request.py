# Copyright (c) 2026, Leapp and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PartnerVerificationRequest(Document):
	def validate(self):
		if self.status in ("Draft", "Submitted", "Under Review", "Rejected"):
			others = frappe.get_all(
				"Partner Verification Request",
				filters={
					"partner": self.partner,
					"status": ("in", ["Draft", "Submitted", "Under Review", "Rejected"]),
					"name": ("!=", self.name or ""),
				},
				limit=1,
			)
			if others:
				frappe.throw(_("This partner already has an open verification request."))
