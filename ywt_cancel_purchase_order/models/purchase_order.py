from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    def button_cancel(self):
        for po_order_id in self:
            for invoice_id in po_order_id.invoice_ids:
                if invoice_id.state != 'cancel':
                    invoice_id.sudo().button_cancel()

            for picking_id in po_order_id.picking_ids:
                if picking_id.state != 'cancel':
                    picking_id.action_cancel()
                    
        return super(PurchaseOrder, self).button_cancel()
