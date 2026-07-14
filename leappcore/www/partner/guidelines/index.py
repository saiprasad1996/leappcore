import frappe


def get_context(context):
	"""Static LEAPP partner guidelines — readable by partners and guests."""
	context.no_cache = 1
	context.show_sidebar = False
	return context
