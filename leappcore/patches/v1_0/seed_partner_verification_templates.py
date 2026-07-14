# Copyright (c) 2026, Leapp and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Seed default Individual/Organisation verification checklists if missing."""
	_ensure_template(
		"Individual",
		"Individual partner verification",
		[
			{
				"field_key": "professional_bio",
				"label": "Professional bio",
				"fieldtype": "Long Text",
				"reqd": 1,
				"description": "Brief summary of your teaching background",
			},
			{
				"field_key": "years_experience",
				"label": "Years of teaching experience",
				"fieldtype": "Int",
				"reqd": 1,
			},
			{
				"field_key": "id_proof",
				"label": "Government ID proof",
				"fieldtype": "Attach",
				"reqd": 1,
				"description": "Upload a clear scan or photo",
			},
			{
				"field_key": "accept_guidelines",
				"label": "I agree to LEAPP partner guidelines",
				"fieldtype": "Check",
				"reqd": 0,
			},
		],
	)
	_ensure_template(
		"Organisation",
		"Organisation partner verification",
		[
			{
				"field_key": "org_overview",
				"label": "Organisation overview",
				"fieldtype": "Long Text",
				"reqd": 1,
			},
			{
				"field_key": "registration_number",
				"label": "Business / registration number",
				"fieldtype": "Text",
				"reqd": 1,
			},
			{
				"field_key": "registration_doc",
				"label": "Registration document",
				"fieldtype": "Attach",
				"reqd": 1,
			},
			{
				"field_key": "contact_person",
				"label": "Primary contact person",
				"fieldtype": "Text",
				"reqd": 1,
			},
			{
				"field_key": "accept_guidelines",
				"label": "I agree to LEAPP partner guidelines",
				"fieldtype": "Check",
				"reqd": 0,
			},
		],
	)


def _ensure_template(partner_type, title, fields):
	if frappe.db.exists("Partner Verification Template", partner_type):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Partner Verification Template",
			"partner_type": partner_type,
			"title": title,
			"is_active": 1,
			"fields": fields,
		}
	)
	doc.insert(ignore_permissions=True)
