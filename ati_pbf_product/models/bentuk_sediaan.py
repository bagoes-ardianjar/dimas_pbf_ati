from odoo import models, fields, _

class bentuk_sediaan(models.Model):
    _name = 'bentuk.sediaan'
    _description = 'Bentuk Sediaan'

    # added by ibad
    name = fields.Char('Bentuk Sediaan')
    
    def unlink(self):
        return super(bentuk_sediaan, self).unlink()