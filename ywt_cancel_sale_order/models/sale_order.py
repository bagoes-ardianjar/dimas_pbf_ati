# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_cancel(self):
        stock_picking_obj = self.env['stock.picking']
        stock_return_obj = self.env['stock.return.picking']
        
        for order_id in self:
            return_picking_ids = stock_return_obj.search([('picking_id', 'in', order_id.picking_ids and order_id.picking_ids.ids)])
            if return_picking_ids:
                for return_picking_id in return_picking_ids:
                    return_picking_id.picking_id.move_lines.update_stock_qty()
            
            for picking_id in order_id.picking_ids:
                if picking_id.state != 'cancel':
                    picking_id.action_cancel()
    
            for invoice_id in order_id.invoice_ids:
                if invoice_id.state == 'paid':
                    invoice_id.line_ids.sudo().remove_move_reconcile()
                    invoice_id.button_cancel()
                else:
                    invoice_id.button_cancel()
        return super(SaleOrder, self).action_cancel()

