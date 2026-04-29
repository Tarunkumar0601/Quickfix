import frappe
import frappe.utils as fu
from frappe.tests.utils import FrappeTestCase

from quickfix.monkey_patches import apply_all


class TestGetUrl(FrappeTestCase):
	def test_get_url_with_and_without_prefix(self):
		# Remove old patch marker if already patched
		if hasattr(fu, "_qf_patched"):
			delattr(fu, "_qf_patched")

		apply_all()

		old_prefix = frappe.conf.get("custom_url_prefix")

		try:
			# With prefix
			frappe.conf["custom_url_prefix"] = "https://cdn.example.com"
			base = fu.get_url("/files/test.txt")
			self.assertIn("https://cdn.example.com", base)

			# Without prefix
			frappe.conf["custom_url_prefix"] = ""
			url2 = fu.get_url("/files/test.txt")
			self.assertNotIn("https://cdn.example.com", url2)

		finally:
			frappe.conf["custom_url_prefix"] = old_prefix
