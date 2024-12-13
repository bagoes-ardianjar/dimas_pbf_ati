# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"


    def _get_po_name(self):
        for account_move in self:
            if account_move.move_type == 'in_refund' and account_move.source_document_id:
                source_picking = account_move.source_document_id.origin.replace('Return of ', '')
                stock_picking_obj = self.env['stock.picking'].search([('name', '=', source_picking)], limit=1)
                if stock_picking_obj:
                    return stock_picking_obj.origin
                else:
                    return False
            else:
                return False
