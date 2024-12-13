from odoo import models, fields, _, api

class StockPickingType(models.Model):
	_inherit = 'stock.picking.type'

	is_receipt = fields.Boolean(string='Is Receipt?')