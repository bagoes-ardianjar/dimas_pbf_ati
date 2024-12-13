# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class StockPickingKoli(models.Model):
    _inherit = "stock.picking.koli"

    wo_batch_id = fields.Many2one('stock.picking.work.order.batch', string='WO Batch Transfer',
        check_company=True, help='WO Batch associated to this transfer', copy=False)