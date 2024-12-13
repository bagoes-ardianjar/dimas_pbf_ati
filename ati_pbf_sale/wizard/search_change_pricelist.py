from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, _, api
from datetime import date
import json

class SearchChangePricelist(models.TransientModel):
	_name = 'search.change.pricelist'
	_description = 'Wizard Pricelist Management'

	def _get_default_currency_id(self):
		return self.env.company.currency_id.id

	@api.depends('pricelist')
	def _compute_check_apply_on(self):
		for pricelist in self.pricelist:
			for item in pricelist.item_ids:
				self.product_in_pricelist |= item

	pricelist = fields.Many2one('product.pricelist', string='Pricelist')
	product_in_pricelist = fields.Many2many('product.pricelist.item', compute='_compute_check_apply_on', readonly=False)
	search_product = fields.Many2many('product.pricelist.item', 'search_product_pricelist_item_rel', string='Product')
	change_product = fields.Many2one('product.pricelist.item', string='Product')
	change_price = fields.Boolean('Change Price')
	old_price = fields.Char('Old Price')
	new_price = fields.Float('New Price', digits='Product Price')
	currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)

	@api.onchange('change_product')
	def _onchange_old_price(self):
		for pricelist in self.pricelist:
			for item in pricelist.item_ids:
				if item.id == self.change_product.id:
					self.old_price = item.price

	@api.onchange('change_price')
	def _onchange_change_price(self):
		view = self.env.ref('ati_pbf_sale.search_change_pricelist_wizard_form')

		for view_ in view:
			if self.change_price == False:
				view_.write({'name': 'Pricelist Product'})
			elif self.change_price == True:
				view_.write({'name': 'Change Pricelist'})

	def search_pricelist(self):
		price_product = []
		for item in self.search_product:
			price_product.append(item.name + ' - ' + item.price)

		view = self.env.ref('sh_message.sh_message_wizard')

		view_id = view and view.id or False
		context = dict(self._context or {})
		context['message'] = '\n\n'.join(price_product)

		return {
			'name': 'Pricelist Product',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'views': [(view.id, 'form')],
			'view_id': view_id,
			'res_model': 'sh.message.wizard',
			'target': 'new',
			'context': context,
		}

	def change_pricelist(self):
		for pricelist in self.pricelist:
			for item in pricelist.item_ids:
				if item.id == self.change_product.id:
					item.write({'fixed_price': self.new_price})

		view = self.env.ref('sh_message.sh_message_wizard')

		view_id = view and view.id or False
		context = dict(self._context or {})
		context['message'] = 'The price has been successfully changed.'

		return {
			'name': 'Change Pricelist Successfully',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'views': [(view.id, 'form')],
			'view_id': view_id,
			'res_model': 'sh.message.wizard',
			'target': 'new',
			'context': context,
		}
