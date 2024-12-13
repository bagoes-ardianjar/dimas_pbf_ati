from odoo import models, fields, _

class PabrikProduct(models.Model):
	_name = 'pabrik.product'
	_description = 'Pabrik'

	# added by ibad
	name = fields.Char('Pabrik')

	def unlink(self):
		return super(PabrikProduct, self).unlink()