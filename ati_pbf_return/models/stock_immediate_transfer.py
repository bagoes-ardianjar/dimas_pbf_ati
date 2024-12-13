from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'


    # delivery status set to Completed
    # def process(self):
    #     res = super(StockImmediateTransfer, self).process()
    #     for rec in self:
    #         if rec.pick_ids:
    #             for pick in rec.pick_ids:
    #                 pick.delivery_status = 'Completed'
    #     return res