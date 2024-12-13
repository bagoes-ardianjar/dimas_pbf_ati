from odoo import models, fields, _

class Checker(models.Model):
    _name = 'checker'
    _description = 'Checker'
    # ...
    name = fields.Char('Checker')