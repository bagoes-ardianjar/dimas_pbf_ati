# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.
import json
from odoo import fields, models, api


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    combo_product_ids = fields.One2many("pos.order.line.combo.products", 'pos_order_id', string="Combo Products")
    datas = fields.Char(string="Datass")


class PosOrder(models.Model):
    _inherit = "pos.order"


class PosOrderLineComboProducts(models.Model):
    _name = 'pos.order.line.combo.products'
    pos_order_id = fields.Many2one('pos.order.line')
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string="quantity")
    product_uom_id = fields.Many2one('uom.uom', string="Uom")
    unit_price = fields.Float(string="Unit price")







