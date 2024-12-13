# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError, Warning


class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    def action_picking_set_draft(self):
        stock_move_obj = self.env['stock.move']
        for picking_id in self:
            move_ids_lst = [move_id.id for move_id in picking_id.move_lines]
            move_ids = stock_move_obj.browse(move_ids_lst)
            if move_ids:
                move_ids.sudo().action_draft()
            move_lines_ids = self.env['stock.move.line'].search([('picking_id', '=', picking_id.id)])
            if move_lines_ids:
              self.env.cr.execute("update stock_move_line set product_qty=0 ,product_uom_qty=0 where id in %s", tuple(move_lines_ids.ids))
        return True
    
    def action_cancel(self):
        account_move_obj = self.env['account.move']
        for picking_id in self:
            picking_id.move_lines.update_stock_qty()
        res = super(StockPicking, self).action_cancel()
        for picking_id in self:
            for move_id in picking_id.move_ids_without_package:
                account_move_ids = account_move_obj.search([('stock_move_id', '=', move_id.id)])
                if account_move_ids:
                    for account_move_id in account_move_ids:
                        account_move_id.line_ids.sudo().remove_move_reconcile()
                        account_move_id.button_cancel()
                        account_move_id.unlink()
        return res
    
