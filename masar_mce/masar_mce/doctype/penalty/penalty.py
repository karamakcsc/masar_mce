# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Penalty(Document):
	def validate(self):
		self.check_type_and_field()
  
	def check_type_and_field(self):
		if self.penalty_type == 'Fixed Value':
			self.penalty_formula = None 
		else: 
			self.penalty_amount = 0 
