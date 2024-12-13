import datetime

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, _, api
from datetime import date, timedelta
import json

class StockPickingBatchIb(models.Model):
    _inherit = 'stock.picking.batch'
    _description = 'Batch Transfer'

    customer = fields.Many2one('res.partner', string='Customer')
    expedition_name = fields.Char('Nama Ekspedisi')
    plat_number = fields.Char('No. Plat')
    driver_name = fields.Char('Nama Supir')

    # koli
    koli_ids = fields.One2many('stock.picking.koli', 'batch_id')

    @api.model
    def create(self, vals):
        res = super(StockPickingBatchIb, self).create(vals)

        for batch in res:
            for picking in batch.picking_ids:
                batch.koli_ids.create({
                    'picking_id': picking.id,
                    'batch_id': batch.id
                })
        return res
    
    def button_print_batch_transfer(self):
        return self.env.ref('ati_pbf_stock.action_report_batch_transfer_custom').report_action(self)