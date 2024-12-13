# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import date, datetime, timedelta
import json


class ati_pbf_report_custom_po(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        payments = self._create_payments()

        active_ids = self.env.context.get("active_ids")
        account = self.env['account.move'].browse(active_ids[0])
        account.payment_date = self.payment_date
        if account.move_type == 'in_invoice':
            self = self.with_context(dont_redirect_to_payments=False)
            account.payment_state = 'not_paid'
            # if account.payment_state == 'not_paid':
            #     for move in account:
            #         tax_totals_json = json.loads(move.tax_totals_json)
            #         move.amount_residual = tax_totals_json['amount_total']

        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action

class account_move(models.Model):
    _inherit = 'account.move'

    payment_date = fields.Date("Payment Date")


