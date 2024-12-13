from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process_cancel_backorder(self):
        res = super().process_cancel_backorder()
        ids_to_change = self._context.get('button_validate_picking_ids')
        doc_ids = self.env['stock.picking'].browse(ids_to_change)
        for doc in doc_ids:
            doc.write({'is_no_backorder': True})
        return res
   

    