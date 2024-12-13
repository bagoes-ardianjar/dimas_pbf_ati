from odoo import models, fields, _, api
from odoo.tools.misc import get_lang
import math

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sales Order Line'


    @api.onchange('product_id')
    def func_onchange_product_id(self):
        if not self.product_id:
            return {}
        else:
            for this in self:
                if this.product_id.product_tmpl_id.standard_price:
                    this.price_unit = this.product_id.product_tmpl_id.standard_price
                elif this.product_id.standard_price:
                    this.price_unit = rec.product_id.standard_price
                else:
                    this.price_unit = False
                if self._origin.id != False:
                    update_data = "update sale_order_line set price_unit = {_price_unit}" \
                                  "where id = {_id}".format(_price_unit=this.price_unit, _id=this._origin.id)
                    self._cr.execute(update_data)
            if self.order_id.state == 'draft':
                if self.is_lock_price != True:
                    if not self.order_id.partner_id.margin_ids or self.order_id.is_pasien == True:
                        if not self.product_id.margin:
                            self.product_margin_percent = '0%'
                        else:
                            self.product_margin_percent = str(self.product_id.margin.name) + '%'
                    else:
                        margin_from_customer = 0
                        for m_margin in self.order_id.partner_id.margin_ids:
                            margin_from_customer += m_margin.value
                            self.product_margin_percent = str(margin_from_customer) + '%'
                else:
                    pass
            else:
                pass
        return {}

    @api.depends('price_unit','product_margin_amount', 'additional_margin')
    def get_harga_satuan(self):
        for this in self:
            if this.id != False:
                if this.product_margin_percent:
                    margin_percent = float(this.product_margin_percent.strip('%'))
                else:
                    margin_percent = 0
                product_margin_amount = this.price_unit * margin_percent / 100
                if this.is_downpayment:
                    this.harga_satuan_baru = round(this.price_unit, 2)
                else:
                    # harga_satuan = ((round(this.price_unit, 2)) + (round(this.product_margin_amount, 2))) + \
                    #                (((round(this.price_unit, 2)) + (round(this.product_margin_amount,2))) *
                    #                 this.additional_margin)
                    harga_satuan = ((round(this.price_unit, 2)) + (round(product_margin_amount, 2))) + \
                                   (((round(this.price_unit, 2)) + (round(product_margin_amount, 2))) *
                                    this.additional_margin)

                    pecahan = harga_satuan % 1
                    satuan = harga_satuan - pecahan

                    if pecahan > 0 or satuan > 0:
                        harga_satuan_baru = math.ceil(harga_satuan / 50) * 50
                        this.harga_satuan_baru = harga_satuan_baru
                    else:
                        harga_satuan_baru = harga_satuan
                        this.harga_satuan_baru = harga_satuan_baru
                    # print(this.product_margin_amount,this.product_margin_percent)
            else:
                this.harga_satuan_baru = 0
                this.harga_satuan = 0

    harga_satuan = fields.Float(string="Harga Satuan Lama", compute=get_harga_satuan)
    harga_satuan_baru = fields.Float(string="Harga Satuan", compute=get_harga_satuan, store=True)
    is_lock_price = fields.Boolean(string="Is Lock Margin", default=False)

    def _checkPrice(self):
        for rec in self:
            is_diff = False
            rec.price_check = False
            if ((round(rec.price_subtotal/rec.product_uom_qty, 2)) < (round(rec.price_unit, 2))):
               is_diff = True

            if is_diff:
               rec.price_check = True


    name = fields.Text(string='Description', required=False)
    ## added by Amal
    price_check = fields.Boolean(compute='_checkPrice', string="Price Check")

    # batch_name = fields.Char(string='Batch')
    # expiration_date = fields.Date(string='Expiration Date')
    # location_name = fields.Char(string='location')

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'harga_satuan')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """

        for line in self:
            nilai_margin_amount = line._compute_product_margin_amount()
            additional_margin = (line.price_unit + round(line.product_margin_amount, 2)) * (line.additional_margin * 100) / 100

            # dis_res = line.price_unit + line.product_margin_amount + additional_margin  # - discount

            dis_res = line.harga_satuan_baru  # - discount
            discount_percent = (line.discount_amount / dis_res) * 100 if line.discount_amount != 0 and dis_res != 0 else 0 # - line.discount_amount or 0.0

            if line.discount != 0 and line.discount_amount == 0:
                discount_amount = (line.discount/100) * dis_res
                line.update({
                    'discount_amount': discount_amount
                })

            # subtotal = (((line.price_unit + round(line.product_margin_amount, 2)) + additional_margin) - (
            #     line.discount_amount))

            subtotal = line.harga_satuan_baru - line.discount_amount

            taxes = line.tax_id.compute_all(subtotal, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)

            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    @api.depends('price_unit', 'discount_amount')
    def _compute_discount(self):
        for line in self:
            nilai_margin_amount = line._compute_product_margin_amount()

            additional_margin = line.price_unit * line.additional_margin / 100
            # dis_res = line.price_unit + nilai_margin_amount + additional_margin  # - discount
            dis_res = line.harga_satuan_baru
            discount = round(((line.discount_amount / dis_res) * 100),2) if line.discount_amount != 0 else 0  # - line.discount_amount or 0.0
            line.discount = round(discount,2)

    # added by ibad
    outstanding_qty = fields.Float('Outstanding Qty', compute='_compute_outstanding_qty')
    discount_amount = fields.Monetary('Disc. Amount')
    special_discount = fields.Boolean(related='order_id.special_discount', string='Special Discount')
    discount = fields.Float(string='Discount (%)', compute='_compute_discount', readonly=False)

    def _compute_outstanding_qty(self):
        for line in self:
            line.outstanding_qty = line.product_uom_qty - line.qty_delivered

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                self.order_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        # self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order,
                               uom=self.product_uom.id)

        price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                               self.product_uom_qty,
                                                                                               self.product_uom,
                                                                                               self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.order_id.pricelist_id.currency_id,
                    self.order_id.company_id or self.env.company, self.order_id.date_order or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                self.discount = discount

    def _update_description(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        product = self.product_id.with_context(
            lang=get_lang(self.env, self.order_id.partner_id.lang).code,
        )

        self.update({'name': product.description})
        # self.update({'name': self.get_sale_order_line_multiline_description_sale(product)})

    @api.depends('order_id.partner_id.margin_ids',
                 'order_id.partner_id.margin_ids.value', 'order_id.is_pasien')
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

    @api.depends('price_unit', 'product_margin_percent')
    def _compute_product_margin_amount(self):
        for prd in self:
            for order_id in self.order_id:
                if order_id.partner_id:
                    for partner in order_id.partner_id:
                        # jika tipe umum (tidak ter-set), ambil margin dari product master
                        if not partner.margin_ids or order_id.is_pasien == True:
                            prd.product_margin_amount = prd.price_unit * prd.product_id.margin.name / 100
                            return prd.product_margin_amount

                        # selain tipe umum, ambil margin dari customer yang mengacu pada model: m.margin
                        else:
                            margin_from_customer = 0
                            for m_margin in partner.margin_ids:
                                margin_from_customer += m_margin.value
                                prd.product_margin_amount = prd.price_unit * margin_from_customer / 100
                                return prd.product_margin_amount
                else:
                    return 0.0

    # product_margin_percent = fields.Char(compute='_compute_product_margin_percent', string='Product Margin (%)', readonly=False)
    product_margin_percent = fields.Char(string='Product Margin (%)', readonly=False)
    product_margin_amount = fields.Float(compute='_compute_product_margin_amount', string='Product Margin', readonly=False)
    additional_margin = fields.Float('Additional Margin (%)', compute='_compute_additional_margin_from_pricelist',
                                     readonly=False)

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

    @api.depends('order_id.pricelist_id.item_ids')
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

    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()

        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            if line.qty_delivered_method == 'stock_move':
                qty = 0.0
                outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
                for move in outgoing_moves:
                    if move.state != 'done':
                        continue
                    qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom,
                                                              rounding_method='HALF-UP')
                for move in incoming_moves:
                    if move.state != 'done':
                        continue
                    qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom,
                                                              rounding_method='HALF-UP')

                line.qty_delivered = qty

                if line.move_ids:
                        for move in line.move_ids:
                            if move.picking_id:
                                for picking in move.picking_id:
                                    if picking.is_return == True:
                                        if picking.state == 'done':
                                            line.qty_delivered -= move.product_uom_qty