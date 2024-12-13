# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import date, datetime, timedelta
import json


class AtiAccountPaymentRegisterIb(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super().action_create_payments()
        if self._context.get('active_model') == 'account.move':
            bill = self.env['account.move'].browse(self._context.get('active_ids'))
            if bill:
                for bill_obj in bill:
                    bill_obj.tukar_faktur = True
        return res