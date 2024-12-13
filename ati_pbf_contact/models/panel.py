from odoo import models, fields, _

class panel(models.Model):
    _name = 'panel.panel'
    _description = 'Panel'

    # added by ibad
    name = fields.Char('Panel')
    partner_id = fields.Many2one('res.partner', 'Partner')