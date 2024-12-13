# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import fields, models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'
    combo_pack = fields.Boolean(string='Combo/Pack')
    combo_sale_price = fields.Selection([('product', 'Main Combo Product'), ('component', 'Component')], string='Sale Price Based On', default='component')
    combo_line = fields.One2many('product.combo.line', 'product_id', string='Product Combo Lines',
                                 copy=True,
                                 auto_join=True)
    id_combo_products = fields.Char(string="combo_id")


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    combo_pack = fields.Boolean(string='Combo/Pack', compute='_combo_pack', inverse='_set_combo_pack')
    combo_sale_price = fields.Selection([('product', 'Main Combo Product'), ('component', 'Component')], string='Sale Price Based On', compute='_combo_sale_price', inverse='_set_combo_sale_price', default='component')
    combo_line = fields.One2many('product.combo.line', 'product_id', string='Product Combo Lines', compute='_combo_pack_line',inverse='_set_combo_line',
                                 copy=True,
                                 auto_join=True)
    id_combo_products = fields.Char(string="combo_id", compute='_combo_product_id', inverse='_set_combo_product_id')

    @api.depends_context('company')
    @api.depends('product_variant_ids', 'product_variant_ids.combo_pack')
    def _combo_pack(self):
        # on the product_product
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.combo_pack = template.product_variant_ids.combo_pack
        for template in (self - unique_variants):
            template.combo_pack = 0.0

    def _set_combo_pack(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.combo_pack = template.combo_pack

    @api.depends_context('company')
    @api.depends('product_variant_ids', 'product_variant_ids.id_combo_products')
    def _combo_product_id(self):
        # on the product_product
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.id_combo_products = template.product_variant_ids.id_combo_products
        for template in (self - unique_variants):
            template.id_combo_products = 0.0

    def _set_combo_product_id(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.id_combo_products = template.id_combo_products

    @api.depends_context('company')
    @api.depends('product_variant_ids', 'product_variant_ids.combo_line')
    def _combo_pack_line(self):
        # on the product_product
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.combo_line = template.product_variant_ids.combo_line
        for template in (self - unique_variants):
            template.combo_line = 0.0

    def _set_combo_line(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.combo_line = template.combo_line

    @api.depends_context('company')
    @api.depends('product_variant_ids', 'product_variant_ids.combo_sale_price')
    def _combo_sale_price(self):
        # on the product_product
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.combo_sale_price = template.product_variant_ids.combo_sale_price
        for template in (self - unique_variants):
            template.combo_sale_price = 0.0

    def _set_combo_sale_price(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.combo_sale_price = template.combo_sale_price