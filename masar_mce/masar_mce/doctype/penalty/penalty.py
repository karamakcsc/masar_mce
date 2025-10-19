# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class Penalty(Document):
	def validate(self):
		self.check_type_and_field()
  
  
	def check_type_and_field(self):
		if self.penalty_type == 'Fixed Value':
			self.penalty_percentage = 0 
		else:
			if self.penalty_percentage < 0 or self.penalty_percentage > 100:
				frappe.throw(_("Penalty Percentage must be between 0 and 100."))
			self.penalty_amount = 0 
		if self.based_on_days == 0: 
			self.auto = 0 
   
