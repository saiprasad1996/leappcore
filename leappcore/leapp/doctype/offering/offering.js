// Copyright (c) 2025, Sai Prasad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Offering", {
	refresh(frm) {
		// nothing extra needed on refresh
	}
});

// When location changes in the Areas child table, clear the area field
// so the user must pick a valid area for the newly selected location.
frappe.ui.form.on("Offering Area Table", {
	location(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "area", null);
	}
});
