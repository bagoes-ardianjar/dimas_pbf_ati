# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import fields, models, api


class ProductComboLine(models.Model):
    _name = 'product.combo.line'
    product_id = fields.Many2one('product.template', string='Product_id', required=True, ondelete='cascade', index=True,
                               copy=False)

    combo_product_id = fields.Many2one(
        'product.product', string='Product',
        change_default=True, ondelete='restrict',
        )
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  ondelete="restrict")
    price = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)

    @api.onchange('combo_product_id')
    def _onchange_combo_product_id(self):
        # print('_onchange_combo_product_id')
        self.price = self.combo_product_id.list_price
        self.uom = self.combo_product_id.uom_id
        self.combo_product_id.id_combo_products = self.product_id.name

