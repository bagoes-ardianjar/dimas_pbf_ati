import re
from odoo import api, fields, Command, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero, float_repr
from odoo.tools.misc import clean_context, format_date
from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION

class HrExpenseSheet(models.Model):
	_inherit = 'hr.expense.sheet'
	_description = 'Expense Sheet'

	def approve_expense_sheets(self):
		self._check_can_approve()

		duplicates = self.expense_line_ids.duplicate_expense_ids.filtered(lambda exp: exp.state in ['approved', 'done'])
		if duplicates:
			action = self.env["ir.actions.act_window"]._for_xml_id('hr_expense.hr_expense_approve_duplicate_action')
			action['context'] = {'default_sheet_ids': self.ids, 'default_expense_ids': duplicates.ids}
			return action
		self._do_approve()
		self.action_sheet_move_create()