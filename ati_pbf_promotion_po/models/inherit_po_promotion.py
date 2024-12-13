from odoo import models, fields, api
import datetime
from datetime import datetime



class ati_pbf_promotion_po_inherit(models.Model):
    _inherit = 'po.promotion'

    @api.onchange('maximum_use_number')
    def onchange_remaining_use(self):
        for rec in self:
            rec.remaining_use_promotion = rec.maximum_use_number

    @api.model
    def create(self, values):

        promotion = self.env['po.promotion'].sudo().search([])

        if values['reward_type'] == 'product':
            values['reward_product_id']
            searchProduct = self.env['product.template'].sudo().search([('id', '=', values['reward_product_id'])])
            name_product = searchProduct.name

            product = self.env['product.product'].sudo().create({
                'name': 'Free product' + ' ' + '-' + ' ' + name_product,
            })

            values['discount_line_product_id'] = product.id
        elif values['reward_type'] == 'discount':
            if values['discount_type'] == 'percentage':
                values['discount_specific_product_ids']

                for data in values['discount_specific_product_ids']:
                    id = data[2]

                    searchProduct = self.env['product.template'].sudo().search([('id', '=', id)])

                    percent = str(values['discount_percentage']) + '%'

                    product = self.env['product.product'].sudo().create({
                        'name': percent + ' ' + 'discount on products',
                    })

                    values['discount_line_product_id'] = product.id

        return super(ati_pbf_promotion_po_inherit, self).create(values)

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'


    _sql_constraints = [
            ('accountable_required_fields',
             "CHECK(1=1)",
             "Missing required fields on accountable purchase order line."),
        ]

    subtotal_diskon = fields.Integer('Sub Total Diskon')
    sequence = fields.Integer('Sequence')
    is_category = fields.Char('Is category')
    name = fields.Text(string='Description', required=False)
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=False)
    price_unit = fields.Float(string='Unit Price', required=False, digits='Product Price')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    is_promotion_ = fields.Boolean('Promotion ? ')
