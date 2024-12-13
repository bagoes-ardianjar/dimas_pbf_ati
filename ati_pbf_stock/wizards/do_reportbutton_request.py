from odoo import models, fields, _, api
from odoo.http import request

class DoReportButtonRequest(models.Model):
	_name = 'do.reportbutton.req'
	_description = 'DO Report Button Req'

	@api.model
	def _default_mail_message_id(self):
		ctx = self.env.context
		if 'active_ids' in ctx:
			msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
													  ('res_id', 'in', ctx['active_ids']),
													  ('is_requested_open_do', '=', True),
													  ('is_approved', '=', False),
													  ('is_rejected', '=', False),
													  ('author_id.user_ids.manager_approval.user_ids.id', '=', self.env.user.id)],
													 order='id asc')


			return msg_id.ids

	mail_message_id = fields.One2many('mail.message', 'do_reportbutton_req', string="Relate to mail.message", default=_default_mail_message_id)