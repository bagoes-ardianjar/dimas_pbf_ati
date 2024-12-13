from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_id_replace_invoice_id = fields.Many2one('account.move', string="Replace Invoice", domain=[], copy=False)