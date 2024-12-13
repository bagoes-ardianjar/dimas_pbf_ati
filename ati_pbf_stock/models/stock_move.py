from odoo import models, fields, _, api

class StockMoveIb(models.Model):
	_inherit = 'stock.move'
	_description = 'Stock Moves'

	# modifdimas
	# def get_expiration_date_helper(self):
	# 	for this in self:
	# 		expiration_date_helper = ''
	# 		sml = self.env['stock.move.line'].sudo().search([
	# 			('move_id', '=', this.id)
	# 		], limit=1)
	# 		if sml:
	# 			expiration_date_helper = sml.expiration_date
	# 			# print('expiration_date_helper',expiration_date_helper)
	# 		this.expiration_date_helper = expiration_date_helper
	#
	# expiration_date_helper = fields.Date(string='Batch', compute=get_expiration_date_helper)

	@api.depends('picking_id.picking_type_id.is_receipt')
	def _dynamic_domain_of_product(self):
		if 'params' in self._context:
			if self._context['params']['model'] == 'stock.picking':
				if 'id' in self._context['params']:
					sm = self.search([('picking_id', '=', self._context['params']['id'])])
					for sm_ in sm:
						for picking_id in sm_.picking_id:
							for picking_type_id in picking_id.picking_type_id:
								if not picking_type_id.is_receipt:
									return "[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('id', '=', product_on_location_id)]"
								elif picking_type_id.is_receipt:
									return "[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"

	@api.depends('picking_id.picking_type_id.is_receipt')
	def _dynamic_domain_of_lot_ids(self):
		if 'params' in self._context:
			if self._context['params']['model'] == 'stock.picking':
				if 'id' in self._context['params']:
					sm = self.search([('picking_id', '=', self._context['params']['id'])])
					for sm_ in sm:
						for picking_id in sm_.picking_id:
							for picking_type_id in picking_id.picking_type_id:
								if not picking_type_id.is_receipt:
									return "[('product_id', '=', product_id), ('id', '=', batch_on_location_id)]"
								elif picking_type_id.is_receipt:
									return "[('product_id', '=', product_id)]"

	product_on_location_id = fields.Many2many('product.product', 'product_on_location_id_rel_move', compute='_compute_product_batch_on_location_id', readonly=False)
	batch_on_location_id = fields.Many2many('stock.production.lot', 'batch_on_location_id_rel_move', compute='_compute_product_batch_on_location_id', readonly=False)
	product_id = fields.Many2one(
		'product.product', 'Product',
		check_company=True,
		domain=_dynamic_domain_of_product,
		index=True, required=True,
		states={'done': [('readonly', True)]})
	lot_ids = fields.Many2many('stock.production.lot', compute='_compute_lot_ids', inverse='_set_lot_ids', domain=_dynamic_domain_of_lot_ids,
							   string='Batch', readonly=False)

	@api.depends('picking_id.location_id')
	def _compute_product_batch_on_location_id(self):
		stock_location = []
		for picking in self.picking_id:
			stock_location.append([location_id.id for location_id in picking.location_id])
		if stock_location:
			self.product_on_location_id = self.env['stock.location'].search([('id', 'in', stock_location[0])]).quant_ids.product_id
			self.batch_on_location_id = self.env['stock.location'].search([('id', 'in', stock_location[0])]).quant_ids.lot_id

	def _get_out_move_lines(self):
		""" Returns the `stock.move.line` records of `self` considered as outgoing. It is done thanks
		to the `_should_be_valued` method of their source and destionation location as well as their
		owner.

		:returns: a subset of `self` containing the outgoing records
		:rtype: recordset
		"""
		res = self.env['stock.move.line']
		for move_line in self.move_line_ids:
			if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
				continue
			if move_line.picking_id.is_return == True:
				if move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued():
					res |= move_line
				elif move_line.location_id._should_be_valued() and not move_line.location_dest_id._should_be_valued():
					res |= move_line
			if move_line.picking_id.is_return == False and move_line.picking_id.picking_type_id != 8:
				if move_line.location_id._should_be_valued() and not move_line.location_dest_id._should_be_valued():
					res |= move_line
		return res