from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, _, api
from datetime import date
import json

class sale_order_reject_apj_ib(models.TransientModel):
    _name = 'sale.order.reject.apj'
    _description = 'Sale Order Reject APJ'

    name = fields.Text('Reason')

    def reject_act_popup(self):
        ctx = dict(self.env.context or {})

        sale_order = self.env['sale.order'].browse(ctx['active_ids'])
        for so in sale_order:
            so.reason_to_reject_apj = self.name
            so.write(
                {
                    'state': 'cancel'
                }
            )