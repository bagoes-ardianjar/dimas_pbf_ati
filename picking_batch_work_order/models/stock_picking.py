# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    wo_batch_id = fields.Many2one('stock.picking.work.order.batch', string='WO Batch Transfer',
        check_company=True, help='WO Batch associated to this transfer', copy=False)
    satuan = fields.Char(string='Satuan', copy=False)
    keterangan = fields.Char(string='Keterangan', copy=False)