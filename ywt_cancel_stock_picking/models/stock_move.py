# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"
    
    def action_draft(self):
        res = self.write({'state':"draft"})
        return res
    
    def _do_unreserve(self):
        for move_id in self:
            for line in move_id.move_line_ids:
                line.state = 'draft'
            move_id.move_line_ids.unlink()
            if move_id.procure_method == 'make_to_order' and not move_id.move_orig_ids:
                move_id.state = 'waiting'
            elif move_id.move_orig_ids and not all(orig_id.state in ('done', 'cancel') for orig_id in move_id.move_orig_ids):
                move_id.state = 'waiting'
            else:
                move_id.state = 'confirmed'
        return True

    def update_stock_qty(self):
        for stock_move_id in self:
            if stock_move_id.state == "done" and stock_move_id.product_id.type == "product":
                for line_id in stock_move_id.move_line_ids:
                    qty = line_id.product_uom_id._compute_quantity(line_id.qty_done, line_id.product_id.uom_id)
                    self.env['stock.quant']._update_available_quantity(line_id.product_id, line_id.location_id, qty, line_id.lot_id  or None, line_id.package_id or None, line_id.owner_id or None)
                    self.env['stock.quant']._update_available_quantity(line_id.product_id, line_id.location_dest_id, qty * -1, line_id.lot_id or None, line_id.package_id  or None , line_id.owner_id or None)
            stock_move_id._action_cancel()
        return True

    def _action_cancel(self):
        for move_id in self:
            move_id._do_unreserve()
            siblings_states = (move_id.move_dest_ids.mapped('move_orig_ids') - move_id).mapped('state')
            if move_id.propagate_cancel:
                if all(state == 'cancel' for state in siblings_states):
                    move_id.move_dest_ids and move_id.move_dest_ids._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move_id.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move_id.move_dest_ids.write({'move_orig_ids': [(3, move_id.id, 0)]})
                    
        self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
        return True
        
