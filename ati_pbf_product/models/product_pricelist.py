from odoo import models, fields, _, api
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class ProductPricelistItem(models.Model):
	_inherit = 'product.pricelist.item'
	_description = 'Product Pricelist Item'

	additional_margin = fields.Float('Additional Margin')