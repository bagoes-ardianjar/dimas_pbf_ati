# -*- coding: utf-8 -*-
######################################################################################
#
#    Odoo Being
#
#    Copyright (C) 2021-TODAY Odoo Being(<https://www.odoobeing.com>).
#    Author: Odoo Being(<https://www.odoobeing.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
from odoo.exceptions import UserError
from odoo import models, fields, api, _


class PosOrderInherit(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrderInherit, self)._order_fields(ui_order)
        combo_list = []
        if ui_order['lines']:
            for l in ui_order['lines']:
                for combo in l[2]['combo_items']:
                    combo_list.append([0, 0, {
                        'product_id': combo['id'],
                        'qty': l[2]['qty'],
                        'full_product_name': combo['name'],
                        'price_unit': float(0.0),
                        'price_subtotal': float(0.0),
                        'price_subtotal_incl': float(0.0),
                    }])
        order_fields['lines'] = order_fields['lines'] + combo_list
        return order_fields


class ComboProduct(models.Model):
    _name = 'combo.product'
    _rec_name = "name"
    _description = 'POS Combo Products'

    name = fields.Char(default="Combo Products")
    is_required = fields.Boolean(string='Is Required')
    category = fields.Many2one('pos.category', string='Category')
    products = fields.Many2many('product.product', 'ob_combo_product_rel')
    combo_id = fields.Many2one('product.template')
    item_count = fields.Integer(string='Item Count')

    @api.onchange('category')
    def _onchange_category(self):
        if self.category:
            return {'domain': {'products': [('pos_categ_id', 'in', self.category.ids)]}}

    @api.onchange('is_required', 'item_count', 'products')
    def _check_limit(self):
        for record in self:
            if record.is_required:
                record.item_count = len(record.products)
            if not record.is_required:
                if record.item_count > len(record.products):
                    raise UserError(_("Selected number of products exceeds allowed item count!"))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_combo = fields.Boolean(string='Is Combo', default=False)
    combo_items = fields.One2many('combo.product', 'combo_id', string='Combo Items')

    @api.onchange('is_combo', 'type')
    def _onchange_combo_type(self):
        for rec in self:
            if rec.is_combo:
                rec.type = 'service'
