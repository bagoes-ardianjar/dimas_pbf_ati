# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    combo_pack = fields.Boolean(string='Combo/Pack')
    combo_sale_price = fields.Selection([('product', 'Main Combo Product'), ('component', 'Component')], string='Sale Price Based On', default='component')
    combo_line = fields.One2many('product.combo.line', 'product_id', string='Product Combo Lines', copy=True,
                                 auto_join=True)
    id_combo_products = fields.Char(string="combo_id")



