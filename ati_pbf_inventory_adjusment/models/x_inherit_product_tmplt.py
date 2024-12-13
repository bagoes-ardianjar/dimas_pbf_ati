from email.policy import default
from odoo import models, fields, _, api

class X_inherit_prod_tmplt(models.Model):
    _inherit = 'product.template'
    _description = ''

    x_minimum_quant = fields.Float(
        'Minimum Qty', default=0, digits='Product Unit of Measure')\

class X_inherit_prod_prod(models.Model):
    _inherit = 'product.product'
    _description = ''

    x_minimum_quant = fields.Float(related="product_tmpl_id.x_minimum_quant", string='Minimum Qty *', default=0, digits='Product Unit of Measure')