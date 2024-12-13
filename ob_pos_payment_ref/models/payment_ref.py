from odoo import models, fields


class PoSOrder(models.Model):
    _inherit = 'pos.order'

    def _payment_fields(self, order, ui_paymentline):
        res = super(PoSOrder, self)._payment_fields(order, ui_paymentline)
        res.update({
            'payment_ref': ui_paymentline.get('payment_ref'),
        })
        return res


class PoSPayment(models.Model):
    _inherit = 'pos.payment'

    payment_ref = fields.Char(string="Payment Reference")