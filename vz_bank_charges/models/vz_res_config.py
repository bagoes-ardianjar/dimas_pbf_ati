from odoo import models, fields, api


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'
    enable_bank_charges = fields.Boolean(string="Enable Bank Charges", defualt=False)


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'
    enable_bank_charges = fields.Boolean(related='company_id.enable_bank_charges', readonly=False)
