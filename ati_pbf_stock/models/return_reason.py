from odoo import models, fields, _

class ReturnReason(models.Model):
    _name = 'return.reason'
    _description = 'Return Reason'

    # added by ibad
    name = fields.Char('Return Reason')