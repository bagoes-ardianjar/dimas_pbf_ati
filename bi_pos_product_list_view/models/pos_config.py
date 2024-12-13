# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
	
class PosConfiguration(models.Model):
	_inherit = 'pos.config'

	enable_list_view = fields.Boolean('Enable List View', default=True)
	display_product_name=fields.Boolean("Display Product Name", default=True)
	display_product_type=fields.Boolean("Display Product Type", default=True)
	display_product_code=fields.Boolean("Display Product Reference Code", default=True)
	display_product_image=fields.Boolean("Display Product Image", default=True)
	display_product_UOM=fields.Boolean("Display Product UOM", default=True)
	display_product_price=fields.Boolean("Display Product Price", default=True)
	display_product_on_hand_qty=fields.Boolean("Display Product On hand Qty", default=True)
	display_product_forecast_qty=fields.Boolean("Display Forecasted Qty", default=True)
	image_size = fields.Selection([
        ('small', 'Small Size'),
        ('medium', 'Medium Size'),
        ('large', 'Large'),],default='medium',)
	default_product_view = fields.Selection([
        ('list', 'List View'),
        ('grid', 'Grid View'),],default='list',)