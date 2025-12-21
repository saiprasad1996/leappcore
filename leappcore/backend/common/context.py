import frappe

class PageContext:
    def __init__(self, context):
        self.context = context

    def get_context(self):
        self.context.main_page = frappe.get_single("Main Page")
        self.context.csrf_token = frappe.sessions.get_csrf_token()
        return self.context
