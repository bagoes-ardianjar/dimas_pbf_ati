from odoo import models, fields, _

class Picker(models.Model):
    _name = 'picker'
    _description = 'Picker'

    name = fields.Char('Picker')