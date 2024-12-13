
from odoo import models, fields, api


class AtiStockPicking(models.Model):
	_inherit = 'stock.picking'
	_description = 'Stock Picking'






	date_deadline = fields.Datetime(
		"Deadline", compute='_compute_date_deadline', store=True, readonly=False,
		help="Date Promise to the customer on the top level document (SO/PO)")




class AtiStockMoveLine(models.Model):
	_inherit = 'stock.move.line'
	_description = 'Stock Move Line'

	@api.depends('picking_id.partner_id')
	def get_picking_partner(self):
		for rec in self:
			rec.picking_contact_id = None
			if rec.picking_id and rec.picking_id.partner_id:
				rec.picking_contact_id = rec.picking_id.partner_id

	def __searchPickingPartner(self, operator, value):
		contact_ids = self.env["res.partner"].search([('name',operator,value)])
		allowed_ids = []
		for ct in contact_ids:
			_ids = self.search([('picking_id.partner_id','=',ct.id)])
			allowed_ids += _ids.ids
		res = [('id', 'in', allowed_ids)]
		return res


	lot_id = fields.Many2one(
		'stock.production.lot', 'Batch',
		domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", check_company=True)
	lot_name = fields.Char('Batch')
	picking_contact_id = fields.Many2one(compute=get_picking_partner, search=__searchPickingPartner, comodel_name='res.partner', readonly=True, string='Partner', store=True)
