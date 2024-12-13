from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons import decimal_precision as dp


class SaleOrderIb(models.Model):
    _inherit = 'sale.order'
    _description = 'Sales Order'

    def action_confirm(self):
        res = super(SaleOrderIb, self).action_confirm()
        product_not_active = []
        for order_line in self.order_line:
            # active_or_not = [product.activate_product for product in order_line.product_id]

            for product in order_line.product_id:
                if product.activate_product == False:
                    if product.sale_ok:
                        product_not_active.append(product.name)


        if not product_not_active:
            return res
        else:
            raise ValidationError(
                _("Product Non Active!\nMenunggu approval manager (manager mengaktifkan produk)\n\nNon-active product:\n%s" % (', \n'.join(product_not_active))))

class SaleOrderLineIb(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sale Order Line'

    @api.depends('product_id.margin', 'product_id.margin.name', 'order_id.partner_id.margin_ids', 'order_id.partner_id.margin_ids.value', 'order_id.is_pasien')
    def _compute_product_margin_percent(self):
        for prd in self:
            for order_id in self.order_id:
                for partner in order_id.partner_id:
                    # jika tipe umum (tidak ter-set), ambil margin dari product master
                    if not partner.margin_ids or order_id.is_pasien == True:
                        if not prd.product_id.margin:
                            prd.product_margin_percent = '0%'
                        else:
                            prd.product_margin_percent = str(prd.product_id.margin.name) + '%'

                    # selain tipe umum, ambil margin dari customer yang mengacu pada model: m.margin
                    else:
                        margin_from_customer = 0
                        for m_margin in partner.margin_ids:
                            margin_from_customer += m_margin.value
                            prd.product_margin_percent = str(margin_from_customer) + '%'

    @api.depends('price_unit', 'product_margin_percent', 'order_id.is_pasien')
    def _compute_product_margin_amount(self):
        for prd in self:
            for order_id in self.order_id:
                for partner in order_id.partner_id:
                    # jika tipe umum (tidak ter-set), ambil margin dari product master
                    if not partner.margin_ids or order_id.is_pasien == True:
                        prd.product_margin_amount = prd.price_unit * prd.product_id.margin.name / 100

                    # selain tipe umum, ambil margin dari customer yang mengacu pada model: m.margin
                    else:
                        margin_from_customer = 0
                        for m_margin in partner.margin_ids:
                            margin_from_customer += m_margin.value
                            prd.product_margin_amount = prd.price_unit * margin_from_customer / 100

    # product_margin_percent = fields.Char(compute='_compute_product_margin_percent', string='Product Margin (%)', store=True)
    product_margin_percent = fields.Char(string='Product Margin (%)', store=True)
    product_margin_amount = fields.Float(compute='_compute_product_margin_amount', string='Product Margin', store=True)
    additional_margin = fields.Float('Additional Margin (%)', compute='_compute_additional_margin_from_pricelist', readonly=False)

    def _set_additional_margin_based_all_product(self, pricelist_item):
        for so_line in self:
            so_line.additional_margin += pricelist_item.additional_margin

    def _set_additional_margin_based_product_categ(self, pricelist_item):
        for so_line in self:
            if so_line.product_id.categ_id.id == pricelist_item.categ_id.id:
                so_line.additional_margin += pricelist_item.additional_margin

    def _set_additional_margin_based_product(self, pricelist_item):
        for so_line in self:
            if so_line.product_id.product_tmpl_id.id == pricelist_item.product_tmpl_id.id:
                so_line.additional_margin += pricelist_item.additional_margin

    def _set_additional_margin_based_product_variant(self, pricelist_item):
        for so_line in self:
            if so_line.product_id.id == pricelist_item.product_id.id:
                so_line.additional_margin += pricelist_item.additional_margin

    @api.depends('order_id.pricelist_id.item_ids.additional_margin')
    def _compute_additional_margin_from_pricelist(self):
        for pricelist in self.order_id.pricelist_id:
            for item in pricelist.item_ids:
                if item.applied_on == '3_global':
                    self._set_additional_margin_based_all_product(item)
                elif item.applied_on == '2_product_category':
                    self._set_additional_margin_based_product_categ(item)
                elif item.applied_on == '1_product':
                    self._set_additional_margin_based_product(item)
                elif item.applied_on == '0_product_variant':
                    self._set_additional_margin_based_product_variant(item)
