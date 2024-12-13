from odoo import models, fields


class PoSPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    enable_payment_ref = fields.Boolean(string="Enable Payment Ref")