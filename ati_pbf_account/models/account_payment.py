from odoo import models, fields, _, api
from datetime import date, datetime, timedelta
import json

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Account Payment'

    def action_cancel(self):
        res = super().action_cancel()
        for rec in self:
            self._cr.execute("""(
                select account_move_id 
                from account_move_account_payment_rel 
                where account_payment_id = {_account_payment_id}
            )""".format(_account_payment_id=rec.id))
            fet = [x[0] for x in self._cr.fetchall()]
            move_id = fet
            # move = self.env['account.move'].search([('name', '=', rec.no_credit_note)])
            for account in move_id:
                move = self.env['account.move'].search([('id', '=', account),('partner_id','=',rec.partner_id.id)])
                if move:
                    for move_obj in move:
                        if move_obj.move_type == 'in_invoice':
                            move_obj.write({'tukar_faktur': False})
        return res