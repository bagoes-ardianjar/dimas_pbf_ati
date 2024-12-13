from odoo import models, fields, _, api
from odoo.http import request
import werkzeug
import werkzeug.wrappers

class MailMessage(models.Model):
	_inherit = 'mail.message'
	_description = 'Mail Message Inherit'

	is_requested_open_do = fields.Boolean('Is Requested Open DO', default=False)
	is_approved = fields.Boolean('Is Approved', default=False)
	is_rejected = fields.Boolean('Is Rejected', default=False)
	do_reportbutton_req = fields.Many2one('do.reportbutton.req')

	def approve(self):
		ctx = self.env.context

		for msg_id in self:
			if msg_id.author_id.user_ids.manager_approval.user_ids.id == self.env.user.id:
				check_for_click = self.env['do.reportbutton.click'].search(
					[('picking_ids', 'in', ctx['active_ids']), ('name', 'in', msg_id.author_id.user_ids.ids)])
				if check_for_click:
					for check_for_click_ in check_for_click:
						check_for_click_.unlink()

				picking_name = self.env['stock.picking'].search([('id', 'in', ctx['active_ids'])], limit=1)
				res_user = self.env['res.users'].search([('id', 'in', msg_id.author_id.user_ids.ids)], limit=1)
				context = dict(self._context or {})
				context['message'] = picking_name.name

				self.env['do.reportbutton.opened'].search([]).unlink()
				self.env['do.reportbutton.opened'].create({'name': 'DO Report Button in ' + picking_name.name + ' Opened for ' + res_user.name})

				action_id = self.env.ref('ati_pbf_stock.action_sh_message_popup_do_report_button_opened')
				base_url = self.env['ir.config_parameter'].get_param('web.base.url')
				base_url += '/web#view_type=form&model=%s&action=%s' % (
					'do.reportbutton.opened',
					action_id.id
				)

				# msg_id = request.env['mail.message'].search([('model', '=', 'stock.picking'),
				# 										  ('res_id', '=', int(id)),
				# 										  ('is_requested_open_do', '=', True),
				# 										  ('is_approved', '=', False),
				# 										  ('is_rejected', '=', False),
				# 										  ('author_id', '=', res_user.partner_id.id)], limit=1, order='id asc')
				msg_id.is_approved = True

				return werkzeug.utils.redirect(base_url)

			elif msg_id.author_id.user_ids.manager_approval.user_ids.id != self.env.user.id:
				picking_name = self.env['stock.picking'].search([('id', 'in', ctx['active_ids'])], limit=1)
				res_user = self.env['res.users'].search([('id', 'in', msg_id.author_id.user_ids.ids)], limit=1)
				context = dict(self._context or {})
				context['message'] = picking_name.name

				self.env['do.reportbutton.denied'].search([]).unlink()
				self.env['do.reportbutton.denied'].create(
					{'name': 'You are not allowed to execute this operation.'})

				action_id = self.env.ref('ati_pbf_stock.action_sh_message_popup_do_report_button_denied')
				base_url = self.env['ir.config_parameter'].get_param('web.base.url')
				base_url += '/web#view_type=form&model=%s&action=%s' % (
					'do.reportbutton.denied',
					action_id.id
				)

				return werkzeug.utils.redirect(base_url)

	def reject(self):
		ctx = self.env.context

		for msg_id in self:
			if msg_id.author_id.user_ids.manager_approval.user_ids.id == self.env.user.id:
				picking_name = self.env['stock.picking'].search([('id', 'in', ctx['active_ids'])], limit=1)
				res_user = self.env['res.users'].search([('id', 'in', msg_id.author_id.user_ids.ids)], limit=1)
				context = dict(self._context or {})
				context['message'] = picking_name.name

				self.env['do.reportbutton.rejected'].search([]).unlink()
				self.env['do.reportbutton.rejected'].create(
					{'name': 'DO Report Button in ' + picking_name.name + ' Rejected for ' + res_user.name})

				action_id = self.env.ref('ati_pbf_stock.action_sh_message_popup_do_report_button_rejected')
				base_url = self.env['ir.config_parameter'].get_param('web.base.url')
				base_url += '/web#view_type=form&model=%s&action=%s' % (
					'do.reportbutton.rejected',
					action_id.id
				)

				# msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
				# 											 ('res_id', '=', int(id)),
				# 											 ('is_requested_open_do', '=', True),
				# 											 ('is_approved', '=', False),
				# 											 ('is_rejected', '=', False),
				# 											 ('author_id', '=', res_user.partner_id.id)], limit=1,
				# 											order='id asc')
				msg_id.is_rejected = True

				return werkzeug.utils.redirect(base_url)

			elif msg_id.author_id.user_ids.manager_approval.user_ids.id != self.env.user.id:
				picking_name = self.env['stock.picking'].search([('id', 'in', ctx['active_ids'])], limit=1)
				res_user = self.env['res.users'].search([('id', 'in', msg_id.author_id.user_ids.ids)], limit=1)
				context = dict(self._context or {})
				context['message'] = picking_name.name

				self.env['do.reportbutton.denied'].search([]).unlink()
				self.env['do.reportbutton.denied'].create(
					{'name': 'You are not allowed to execute this operation.'})

				action_id = self.env.ref('ati_pbf_stock.action_sh_message_popup_do_report_button_denied')
				base_url = self.env['ir.config_parameter'].get_param('web.base.url')
				base_url += '/web#view_type=form&model=%s&action=%s' % (
					'do.reportbutton.denied',
					action_id.id
				)

				return werkzeug.utils.redirect(base_url)