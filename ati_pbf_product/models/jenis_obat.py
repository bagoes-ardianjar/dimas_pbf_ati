from odoo import models, fields, _

class jenis_obat(models.Model):
    _name = 'jenis.obat'
    _description = 'Jenis Obat'

    # added by ibad...
    name = fields.Char('Jenis Obat')

    def unlink(self):
        return super(jenis_obat, self).unlink()