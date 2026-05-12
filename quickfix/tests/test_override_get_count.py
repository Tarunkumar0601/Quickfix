import frappe
from frappe.tests.utils import FrappeTestCase

from quickfix.api import custom_get_count


class TestOverrideGetCount(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Audit Log", {})

	def test_override_is_called(self):
		custom_get_count("DocType")

		log = frappe.db.exists("Audit Log", {"doctype_name": "DocType", "action": "count_queried"})

		self.assertIsNotNone(log)

	def test_hook_registered(self):
		hooks = frappe.get_hooks("override_whitelisted_methods")
		self.assertIn("frappe.client.get_count", hooks)
