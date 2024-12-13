# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188o
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GirAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Giro'

    @api.depends('can_edit_wizard', 'company_id')
    def _compute_journal_id(self):
        for wizard in self:
            wizard.journal_id = False
            # if wizard.can_edit_wizard:
            #     batch = wizard._get_batches()[0]
            #     wizard.journal_id = wizard._get_batch_journal(batch)
            # else:
            #     wizard.journal_id = self.env['account.journal'].search([
            #         ('type', 'in', ('bank', 'cash')),
            #         ('company_id', '=', wizard.company_id.id),
            #     ], limit=1)

    is_giro = fields.Boolean(string='Giro')
    tgl_giro = fields.Date(string='Tanggal Giro')
    no_check = fields.Char(string='No Cek')
    payment_method = fields.Char("Related Payment Method", related="payment_method_line_id.name")

    @api.onchange('tgl_giro')
    def onchange_tgl_giro(self):
        if self.tgl_giro:
            self.payment_date = self.tgl_giro


    def _create_payments(self):
        ctx = self._context
        active_ids = ctx.get('active_ids')
        active_model = ctx.get('active_model')
        doc_ids = self.env[active_model].sudo().browse(active_ids)
        pay = super(GirAccountPaymentRegister, self)._create_payments()
        if pay.reconciled_bill_ids and pay.reconciled_bill_ids.filtered(lambda x: x.move_type == 'in_invoice'):
            pay.update({'temp_bill': pay.reconciled_bill_ids.ids})
            pay.action_draft()
            pay.update({
                'is_giro' : self.is_giro,
                'tgl_giro' : self.tgl_giro,
                'no_check' : self.no_check,
                'no_credit_note' : ', '.join([doc.name for doc in doc_ids]),
                })
            return pay
        pay.update({
            'is_giro' : self.is_giro,
            'tgl_giro' : self.tgl_giro,
            'no_check' : self.no_check,
            'no_credit_note' : ', '.join([doc.name for doc in doc_ids]),
            })
        return pay
