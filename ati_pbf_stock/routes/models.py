from odoo import http, fields, registry
from odoo.http import request, route
from odoo.tools.config import config
# from odoo.addons.restful.common import invalid_response, valid_response
from odoo.exceptions import AccessDenied, AccessError
import xmlrpc.client
import werkzeug
import werkzeug.wrappers
import datetime
import functools
import json
import base64
import logging
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT,\
    DEFAULT_SERVER_DATE_FORMAT

class Approve(http.Controller):
	@route('/web/approve', type='http', auth='user', website=True, sitemap=False)
	def open_do_report_button(self, token, db, user_id, id, view_id, requestor, manager, do_number, requestor_email, manager_email, requestor_id, user):
		# check_for_click = request.env['do.reportbutton.click'].search([('picking_ids', '=', int(id)), ('name', '=', int(user_id))])
		# if check_for_click:
		# 	for check_for_click_ in check_for_click:
		# 		check_for_click_.unlink()

		if int(user) == request.env.user.id:
			check_for_click = request.env['do.reportbutton.click'].search(
				[('picking_ids', '=', int(id)), ('name', '=', int(user_id))])
			if check_for_click:
				for check_for_click_ in check_for_click:
					check_for_click_.unlink()

			picking_name = request.env['stock.picking'].search([('id', '=', int(id))], limit=1)
			res_user = request.env['res.users'].search([('id', '=', int(user_id))], limit=1)
			context = dict(request._context or {})
			context['message'] = picking_name.name

			request.env['do.reportbutton.opened'].search([]).unlink()
			request.env['do.reportbutton.opened'].create({'name': 'DO Report Button in ' + picking_name.name + ' Opened for ' + res_user.name})

			action_id = request.env.ref('ati_pbf_stock.action_sh_message_popup_do_report_button_opened')
			base_url = request.env['ir.config_parameter'].get_param('web.base.url')
			base_url += '/web#view_type=form&model=%s&action=%s' % (
				'do.reportbutton.opened',
				action_id.id
			)

			msg_id = request.env['mail.message'].search([('model', '=', 'stock.picking'),
													  ('res_id', '=', int(id)),
													  ('is_requested_open_do', '=', True),
													  ('is_approved', '=', False),
													  ('is_rejected', '=', False),
													  ('author_id', '=', res_user.partner_id.id)], limit=1, order='id asc')
			msg_id.is_approved = True

			return werkzeug.utils.redirect(base_url)

		elif int(user) != request.env.user.id:
			picking_name = request.env['stock.picking'].search([('id', '=', int(id))], limit=1)
			res_user = request.env['res.users'].search([('id', '=', int(user_id))], limit=1)
			context = dict(request._context or {})
			context['message'] = picking_name.name

			request.env['do.reportbutton.denied'].search([]).unlink()
			request.env['do.reportbutton.denied'].create(
				{'name': 'You are not allowed to execute this operation.'})

			action_id = request.env.ref('ati_pbf_stock.action_sh_message_popup_do_report_button_denied')
			base_url = request.env['ir.config_parameter'].get_param('web.base.url')
			base_url += '/web#view_type=form&model=%s&action=%s' % (
				'do.reportbutton.denied',
				action_id.id
			)

			return werkzeug.utils.redirect(base_url)


	@route('/web/reject', type='http', auth='user', website=True, sitemap=False)
	def reject_do_report_button(self, token, db, user_id, id, view_id, requestor, manager, do_number,
							  requestor_email, manager_email, user):
		if int(user) == request.env.user.id:
			picking_name = request.env['stock.picking'].search([('id', '=', int(id))], limit=1)
			res_user = request.env['res.users'].search([('id', '=', int(user_id))], limit=1)
			context = dict(request._context or {})
			context['message'] = picking_name.name

			request.env['do.reportbutton.rejected'].search([]).unlink()
			request.env['do.reportbutton.rejected'].create(
				{'name': 'DO Report Button in ' + picking_name.name + ' Rejected for ' + res_user.name})

			action_id = request.env.ref('ati_pbf_stock.action_sh_message_popup_do_report_button_rejected')
			base_url = request.env['ir.config_parameter'].get_param('web.base.url')
			base_url += '/web#view_type=form&model=%s&action=%s' % (
				'do.reportbutton.rejected',
				action_id.id
			)

			msg_id = request.env['mail.message'].search([('model', '=', 'stock.picking'),
														 ('res_id', '=', int(id)),
														 ('is_requested_open_do', '=', True),
														 ('is_approved', '=', False),
														 ('is_rejected', '=', False),
														 ('author_id', '=', res_user.partner_id.id)], limit=1,
														order='id asc')
			msg_id.is_rejected = True

			return werkzeug.utils.redirect(base_url)

		elif int(user) != request.env.user.id:
			picking_name = request.env['stock.picking'].search([('id', '=', int(id))], limit=1)
			res_user = request.env['res.users'].search([('id', '=', int(user_id))], limit=1)
			context = dict(request._context or {})
			context['message'] = picking_name.name

			request.env['do.reportbutton.denied'].search([]).unlink()
			request.env['do.reportbutton.denied'].create(
				{'name': 'You are not allowed to execute this operation.'})

			action_id = request.env.ref('ati_pbf_stock.action_sh_message_popup_do_report_button_denied')
			base_url = request.env['ir.config_parameter'].get_param('web.base.url')
			base_url += '/web#view_type=form&model=%s&action=%s' % (
				'do.reportbutton.denied',
				action_id.id
			)

			return werkzeug.utils.redirect(base_url)
