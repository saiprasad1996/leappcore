import frappe
from frappe.exceptions import DoesNotExistError
from leappcore.backend.common.context import PageContext


def get_context(context):
    context = PageContext(context).get_context()
    context.no_cache = 1

    blog_id = frappe.form_dict.get("id")
    if not blog_id:
        frappe.local.flags.redirect_location = "/blogs/list"
        raise frappe.Redirect

    try:
        doc = frappe.get_doc("NewsBlogs", blog_id)
        if not doc.published:
            raise DoesNotExistError
        context.blog = doc
    except DoesNotExistError:
        context.show_404 = True
        context.blog_id = blog_id
        frappe.response["http_status_code"] = 404

    return context
