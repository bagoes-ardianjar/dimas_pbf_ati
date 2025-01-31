# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class StockPickingToBatchWorkOrder(models.TransientModel):
    _name = 'stock.picking.to.batch.work.order'
    _description = 'Batch Transfer Lines'

    wo_batch_id = fields.Many2one('stock.picking.work.order.batch', string='Work Order Batch Transfer')
    mode = fields.Selection([('existing', 'an existing batch transfer'), ('new', 'a new batch transfer')], default='existing')
    user_id = fields.Many2one('res.users', string='Responsible', help='Person responsible for this batch transfer')

    def attach_pickings(self):
        self.ensure_one()
        pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        if self.mode == 'new':
            company = pickings.company_id
            if len(company) > 1:
                raise UserError(_("The selected pickings should belong to an unique company."))
            wo_batch = self.env['stock.picking.work.order.batch'].create({
                'user_id': self.user_id.id,
                'company_id': company.id,
                'picking_type_id': pickings[0].picking_type_id.id,
            })
        else:
            wo_batch = self.batch_id

        pickings.write({'wo_batch_id': wo_batch.id})
