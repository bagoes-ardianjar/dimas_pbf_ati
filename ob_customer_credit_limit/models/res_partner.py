# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_check = fields.Boolean('Active Credit', help='Activate the credit limit feature')
    credit_warning = fields.Monetary('Warning Amount')
    credit_blocking = fields.Monetary('Blocking Amount')
    amount_due = fields.Monetary('Due Amount', compute='_compute_amount_due')
    remaining_credit = fields.Monetary('Remaining Credit', compute='_compute_remaining_credit')

    @api.depends('credit', 'debit')
    def _compute_remaining_credit(self):
        for rec in self:
            if rec.credit_check != False:
                rec.remaining_credit = rec.credit_blocking - rec.credit
            else:
                rec.remaining_credit = 0

    @api.depends('credit', 'credit_blocking')
    def _compute_amount_due(self):
        for rec in self:
            rec.amount_due = rec.credit - rec.debit

    @api.constrains('credit_warning', 'credit_blocking')
    def _check_credit_amount(self):
        for credit in self:
            if credit.credit_blocking < 0:
                raise ValidationError(_('Blocking amount should not be less than zero.'))
            # if credit.credit_warning > credit.credit_blocking:
            #     print('aaaaa')
            #     raise ValidationError(_('Warning amount should not be greater than blocking amount.'))
            # if credit.credit_warning < 0 or credit.credit_blocking < 0:
            #     raise ValidationError(_('Warning amount or blocking amount should not be less than zero.'))
