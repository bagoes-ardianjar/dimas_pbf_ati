from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, _, api
from datetime import date
import json

class quotation_confirm(models.TransientModel):
    _name = 'quotation.confirm'
    _description = 'Quotation Confirm'

    def confirm_quotation(self):
        ctx = dict(self.env.context or {})
        sale_order = self.env['sale.order'].browse(ctx['active_ids'])
        for so in sale_order:
            so.write(
                {
                    'state': 'waiting_approval_apj'
                }
            )