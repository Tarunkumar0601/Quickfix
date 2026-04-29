import frappe


def apply_all():
	_patch_get_url()


def _patch_get_url():
	import frappe.utils as fu

	if hasattr(fu, "_qf_patched"):
		return

	fu._qf_original_get_url = fu.get_url

	def _custom_get_url(path=None, full_address=False):
		url = fu._qf_original_get_url(path, full_address)
		prefix = frappe.conf.get("custom_url_prefix") or ""
		return f"{prefix}{url}" if prefix else url

	fu.get_url = _custom_get_url
	fu._qf_patched = True
