# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

class ReturnPickingIb(models.TransientModel):
	_inherit = 'stock.return.picking'

	# ...
	location_id = fields.Many2one(
		'stock.location', 'Return Location',
		domain="['|', ('id', '=', original_location_id), '|', ('return_location', '=', True), ('company_id', '=', False)]")

	@api.onchange('picking_id')
	def _onchange_picking_id(self):
		move_dest_exists = False
		product_return_moves = [(5,)]
		print('product_return',product_return_moves)
		if self.picking_id and self.picking_id.state != 'done':
			raise UserError(_("You may only return Done pickings."))
		# In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
		# default values for creation.
		line_fields = [f for f in self.env['stock.return.picking.line']._fields.keys()]
		product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
		print('product_return_templ', product_return_moves_data_tmpl)
		for move in self.picking_id.move_lines:
			if move.state == 'cancel':
				continue
			if move.scrapped:
				continue
			if move.move_dest_ids:
				move_dest_exists = True
			product_return_moves_data = dict(product_return_moves_data_tmpl)
			print('product_return_data', product_return_moves_data)
			product_return_moves_data.update(self._prepare_stock_return_picking_line_vals_from_move(move))
			product_return_moves.append((0, 0, product_return_moves_data))
			print('product_return_data_update', product_return_moves_data)
			print('product_return_move', product_return_moves)
		if self.picking_id and not product_return_moves:
			raise UserError(
				_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
		if self.picking_id:
			self.product_return_moves = product_return_moves
			self.move_dest_exists = move_dest_exists
			self.parent_location_id = self.picking_id.picking_type_id.warehouse_id and self.picking_id.picking_type_id.warehouse_id.view_location_id.id or self.picking_id.location_id.location_id.id
			self.original_location_id = self.picking_id.location_id.id
			self.product_return_moves.original_lot_id = self.env['stock.production.lot'].browse(self.picking_id.move_lines.lot_ids.ids).ids
			location_id = self.picking_id.location_id.id
			if self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
				location_id = self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
			self.location_id = location_id

	@api.model
	def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
		quantity = stock_move.product_qty
		for move in stock_move.move_dest_ids:
			if move.origin_returned_move_id and move.origin_returned_move_id != stock_move:
				continue
			if move.state in ('partially_available', 'assigned'):
				quantity -= sum(move.move_line_ids.mapped('product_qty'))
			elif move.state in ('done'):
				quantity -= move.product_qty
		quantity = float_round(quantity, precision_rounding=stock_move.product_id.uom_id.rounding)
		return {
			'product_id': stock_move.product_id.id,
			'quantity_check': quantity,
			'quantity_done': stock_move.quantity_done,
			'quantity': 0.0,
			'move_id': stock_move.id,
			'uom_id': stock_move.product_id.uom_id.id,
			'lot_id': stock_move.lot_ids.ids,
		}

	def _create_returns(self):
		for move in self.picking_id.move_lines:
			line_value = self._prepare_stock_return_picking_line_vals_from_move(move)

			for line_retur in self.product_return_moves:

				if line_retur.product_id.id == line_value.get('product_id'):
					if line_value.get('quantity_check') > 0:
						if line_retur.quantity > line_value.get('quantity_check'):
							raise UserError(_('Over quantity'))
					elif line_value.get('quantity_check') == 0:
						if line_retur.quantity > line_value.get('quantity_check'):
							raise UserError(_('All returned'))
			
		return super(ReturnPickingIb, self)._create_returns()

class ReturnPickingLineIb(models.TransientModel):
	_inherit = 'stock.return.picking.line'

	original_lot_id = fields.Many2many('stock.production.lot', 'return_picking_rel', string='Original Lot ID')
	lot_id = fields.Many2many('stock.production.lot', string='Batch')
	quantity = fields.Float("Qty to Retur", digits='Product Unit of Measure', required=True, default=0.0)
	quantity_check = fields.Float("Qty Check", digits='Product Unit of Measure')
	quantity_done = fields.Float("Qty Done", digits='Product Unit of Measure')
	product_id = fields.Many2one('product.product', string="Product", required=True, domain="")