from odoo import models, fields, api, _


class AccountJournalInherit(models.Model):
    _inherit = "account.journal"

    bank_charge_account = fields.Many2one('account.account')
