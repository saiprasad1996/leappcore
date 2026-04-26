// Copyright (c) 2025, Sai Prasad and contributors
// For license information, please see license.txt

function set_area_query(frm) {
	frm.set_query("area", () => {
		if (frm.doc.location) {
			return {
				filters: { location: frm.doc.location },
			};
		}
		// No city selected: show no areas until City is chosen
		return { filters: { name: ["=", ""] } };
	});
}

frappe.ui.form.on("Leapp Event", {
	refresh(frm) {
		set_area_query(frm);
	},

	location(frm) {
		if (!frm.doc.location) {
			frm.set_value("area", "");
			set_area_query(frm);
			return;
		}
		if (!frm.doc.area) {
			set_area_query(frm);
			return;
		}
		frappe.db.get_value("Area", frm.doc.area, "location", (r) => {
			if (!r || r.location !== frm.doc.location) {
				frm.set_value("area", "");
			}
			set_area_query(frm);
		});
	},
});
