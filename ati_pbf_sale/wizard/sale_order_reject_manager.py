from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, _, api
from datetime import date
import json

class sale_order_reject_manager_ib(models.TransientModel):
    _name = 'sale.order.reject.manager'
    _description = 'Sale Order Reject Manager'

    name = fields.Text('Reason')

    def reject_act_popup(self):
        ctx = dict(self.env.context or {})

        sale_order = self.env['sale.order'].browse(ctx['active_ids'])
        for so in sale_order:
            so.reason_to_reject_manager = self.name
            so.write(
                {
                    'state': 'cancel'
                }
            )