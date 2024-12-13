from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons import decimal_precision as dp

class PurchaseOrderIb(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Order'

    id_of_supplierinfo = fields.Integer('ID of Supplierinfo')

    def button_confirm(self):
        res = super(PurchaseOrderIb, self).button_confirm()
        product_not_active = []
        for order_line in self.order_line:
            # active_or_not = [product.activate_product for product in order_line.product_id]

            for product in order_line.product_id:
                if product.activate_product == False:
                    product_not_active.append(product.name)

            for prd in order_line.product_id:
                for seller in prd.seller_ids:
                    order_line.order_id.id_of_supplierinfo = seller.id # ...

        if not product_not_active:
            return res
        else:
            raise ValidationError(_("Product Non Active!\nMenunggu approval manager (manager mengaktifkan produk)\n\nNon-active product:\n%s" % (
                    ', \n'.join(product_not_active))))

class PurchaseOrderLineIb(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'

    @api.depends('product_id.margin', 'product_id.margin.name')
    def _compute_product_margin_percent(self):
        for prd in self:
            if not prd.product_id.margin:
                prd.product_margin_percent = '0%'
            else:
                prd.product_margin_percent = str(prd.product_id.margin.name) + '%'

    @api.depends('price_unit', 'product_margin_percent')
    def _compute_product_margin_amount(self):
        for prd in self:
            prd.product_margin_amount = prd.price_unit * prd.product_id.margin.name / 100

    product_margin_percent = fields.Char(compute='_compute_product_margin_percent', string='Product Margin (%)', store=True)
    product_margin_amount = fields.Float(compute='_compute_product_margin_amount', string='Product Margin', store=True)
    additional_margin = fields.Float('Additional Margin (%)')