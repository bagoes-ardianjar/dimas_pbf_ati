from odoo import api, models, fields, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def reset_loyalty(self):
        # print("loyalty")
        partners = self.env['res.partner'].search([('active', '=', True)])

        for rec in partners:
            # print("loyalty", rec.name, rec.loyalty_points)
            if rec.loyalty_points > 0:
                rec.write({'loyalty_points': 0})

        return True