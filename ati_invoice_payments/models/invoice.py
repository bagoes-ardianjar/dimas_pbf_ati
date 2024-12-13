# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AtiAccounts(models.Model):
    _inherit = 'account.move'
    _description = 'invoice payments'

    date_tax_number = fields.Date(string='Tanggal Faktur Pajak',)

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

    def action_register_payment(self):
        ''' 
        Override method odoo in modul account folder models file account_move.py
        '''
        ctx = {
            'active_model': 'account.move',
            'active_ids': self.ids,
            'default_communication': ', '.join(mv.ref if mv.ref else mv.name if mv.move_type == 'in_invoice' else mv.ref if mv.ref else mv.name for mv in self)
        }
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': ctx,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
