import frappe

from quickfix.quickfix.doctype.job_card.job_card import JobCard


# Method Resolution Order (MRO) note:
# Python resolves methods using the class MRO (for this class, CustomJobCard -> JobCard -> Document -> object).
# Calling super().validate() is non-negotiable because the base JobCard.validate() enforces core validation
# and calculations. Skipping super() would bypass existing business rules and create inconsistent document state.
#
# override_doctype_class vs doc_events:
# Use override_doctype_class when you need full controller behavior (inheritance, method composition, private
# helper methods, or replacing method internals while still reusing base logic through super()).
# Use doc_events when you only need event callbacks attached externally and do not need to replace controller code.
class CustomJobCard(JobCard):
	def validate(self):
		super().validate()
		self._check_urgent_unassigned()

	def _check_urgent_unassigned(self):
		if self.priority == "Urgent" and not self.assigned_technician:
			settings = frappe.get_single("QuickFix Settings")
			if settings.manager_email:
				frappe.enqueue(
					"quickfix.utils.send_urgent_alert",
					job_card=self.name,
					manager=settings.manager_email,
				)
