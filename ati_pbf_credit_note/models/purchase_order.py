from odoo import api, fields, models, _


class Purchase(models.Model):
    _inherit = 'purchase.order'


    def _prepare_invoice(self):
        res = super(Purchase, self)._prepare_invoice()
        bill = self._context.get('create_bill')
        if bill == True and self._name == 'purchase.order' and self.effective_date:
            res['invoice_date'] = self.effective_date
        return res