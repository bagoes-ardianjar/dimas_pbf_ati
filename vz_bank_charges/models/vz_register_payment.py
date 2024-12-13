from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentRegisterInherit(models.TransientModel):
    _inherit = 'account.payment.register'
    vz_bank_charge = fields.Float()

    is_bank = fields.Boolean(default=False)

    @api.onchange('journal_id')
    def _onchange_vz_bank_journal(self):
        if self.journal_id.type == 'bank' and self.env.company.enable_bank_charges:
            self.is_bank = True
        else:
            self.is_bank = False

    def _create_payment_vals_from_wizard(self):
        res = super(PaymentRegisterInherit, self)._create_payment_vals_from_wizard()
        res['vz_bank_charge'] = self.vz_bank_charge
        res['enable_charge'] = self.is_bank
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        res = super(PaymentRegisterInherit, self)._create_payment_vals_from_batch(batch_result)
        res['vz_bank_charge'] = self.vz_bank_charge
        res['enable_charge'] = self.is_bank
        return res

    def action_create_payments(self):
        for rec in self:
            if rec.vz_bank_charge < 0:
                raise ValidationError(_("You are not allowed to select a negative value"))
            if rec.journal_id.type == 'bank' and not rec.journal_id.bank_charge_account:
                raise ValidationError(_("Please set bank charge account in the selected journal."))
        return super(PaymentRegisterInherit, self).action_create_payments()
