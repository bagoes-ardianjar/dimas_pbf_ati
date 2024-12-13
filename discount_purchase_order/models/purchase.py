# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from num2words import num2words

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    @api.depends( 'order_line.discount_type',
                  'global_order_discount',
                 'global_discount_type')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = total_discount = 0.0
            sumSubTotal = 0
            taxes = 0
            tax_pph = 0
            for line in order.order_line:
                if order.global_discount_type == 'fixed':
                    sumSubTotal += line.line_sub_total
                    total_global_discount = order.global_order_discount
                else:
                    sumSubTotal += line.line_sub_total
                    calculate_global_diskon = sumSubTotal * order.global_order_discount / 100
                    total_global_discount = calculate_global_diskon

                line._compute_amount()


                for tax_id in line.taxes_id:
                    if tax_id.tax_group_id.name == 'PPN':
                        taxes = tax_id.amount
                    if tax_id.tax_group_id.name == 'PPH 22':
                        tax_pph = tax_id.amount

                amount_untaxed += line.line_sub_total
                amount_untaxedtotal = amount_untaxed + line.subtotal_diskon

                if line.discount_type == 'fixed':
                    amount_disc1 = line.ati_price_unit * line.discount_1 / 100
                    amount_disc2 = line.ati_price_unit * line.discount_2 / 100
                    total_discount += ((amount_disc1 + amount_disc2 + line.discount_3 + line.discount_4) * line.product_qty)
                else:
                    amount_disc1 = line.ati_price_unit * line.discount_1 / 100
                    amount_disc2 = line.ati_price_unit * line.discount_2 / 100
                    total_discount += ((amount_disc1 + amount_disc2 + line.discount_3 + line.discount_4) * line.product_qty)

                IrConfigPrmtrSudo = self.env['ir.config_parameter'].sudo()
                discTax = IrConfigPrmtrSudo.get_param('account.global_discount_tax')

                amount_tax = (amount_untaxedtotal - total_global_discount) * taxes / 100
                amount_pph = (amount_untaxedtotal - total_global_discount) * tax_pph / 100
                total = (amount_untaxedtotal - total_global_discount) + amount_tax + amount_pph
                total_word = round(total,2)
                currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id

                order.update({
                    'amount_untaxed': currency.round(amount_untaxedtotal),
                    'amount_tax': currency.round(amount_tax),
                    'amount_pph': currency.round(amount_pph),
                    'amount_total': currency.round(total),
                    'total_global_discount': currency.round(total_global_discount),
                    'total_discount': currency.round(total_discount),
                    'word_num': str(num2words(total_word, lang='id'))
                })

    total_global_discount = fields.Monetary(string='Total Global Discount', store=True,
                                            readonly=True, compute='_amount_all')
    total_global_discount1 = fields.Monetary(string='Total Global Discount', store=True,
                                            readonly=True, compute='_amount_all')
    total_discount = fields.Monetary(string='Total Discount', readonly=False,
                                     compute='_amount_all', tracking=True)
    word_num = fields.Char(string="Amount In Words:", compute='_amount_all', readonly=False)
    global_discount_type = fields.Selection(
        [('fixed', 'Fixed'), ('percent', 'Percent')],
        string="Discount Type",
        default="percent",
        help="If global discount type 'Fixed' has been applied then no partial invoice will be generated for this order.")
    global_order_discount = fields.Float(string='Global Discount', store=True, tracking=True)
    amount_pph = fields.Monetary(string='PPH 22', store=True, readonly=True, compute='_amount_all')

    def _prepare_invoice(self):
        self.ensure_one()
        if self.global_order_discount and not self.env.company.discount_account_bill:
            raise UserError(
                _("Global Discount!\nPlease first set account for global discount in purchase setting."))
        # if self.global_order_discount and self.global_discount_type == 'fixed':
        #     lines = self.order_line.filtered(
        #         lambda l: l.product_id.purchase_method != 'purchase' and l.product_qty != l.qty_received)
        #     if lines:
        #         raise UserError(
        #             _("This action is going to make bill invoice for the less quantity recieved of this order.\n It will not be allowed because 'Fixed' type global discount has been applied."))
        vals = super(PurchaseOrder, self)._prepare_invoice()
        vals.update({
            'global_discount_type': self.global_discount_type,
            'global_order_discount': self.global_order_discount,
            'amount_pph': self.amount_pph,
            'is_from_po': True,
        })
        return vals


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # @api.depends('price_unit', 'discount_type', 'discount_1', 'discount_2', 'discount_3', 'discount_4', 'taxes_id', 'product_qty')
    # def _get_line_subtotal(self):
    #     for line in self:
    #         price = line.price_unit
    #         quantity = line.product_qty
    #         taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, quantity,
    #                                           product=line.product_id, partner=line.order_id.partner_id)
    #         line.line_sub_total = taxes['total_excluded']



    #         if line.discount_1:
    #             before_discount = line.price_unit
    #             discount = line.price_unit * line.discount_1 / 100
    #             after_discount = (before_discount - discount) * line.product_qty
    #             line.line_sub_total = after_discount


    #         if line.discount_2:
    #             before_discount = line.price_unit

    #             discount2 = line.price_unit * line.discount_2 / 100
    #             discount = line.price_unit * line.discount_1 / 100
    #             after_discount2 = (before_discount - discount - discount2) * line.product_qty
    #             line.line_sub_total = after_discount2


    #         if line.discount_3:

    #             discount1 = line.price_unit * line.discount_1 / 100
    #             discount2 = line.price_unit * line.discount_2 / 100
    #             result_price_unit = (line.price_unit - line.discount_3 - discount1 - discount2) * line.product_qty

    #             line.line_sub_total = result_price_unit

    #         if line.discount_4:
    #             discount1 = line.price_unit * line.discount_1 / 100
    #             discount2 = line.price_unit * line.discount_2 / 100
    #             result_price_unit = (line.price_unit - line.discount_4 - line.discount_3 - discount2 - discount1) * line.product_qty
    #             line.line_sub_total = result_price_unit

    @api.depends('price_unit', 'discount_type', 'discount_1', 'discount_2', 'discount_3', 'discount_4', 'taxes_id', 'product_qty', 'ati_price_unit')
    def _get_line_subtotal(self):
        for line in self:
            price_unit = line.ati_price_unit

            if line.discount_1:
                if line.discount_1 >= 100:
                    discount = price_unit
                else:
                    discount = price_unit * line.discount_1 / 100
                price_unit = price_unit - discount
            if line.discount_2:
                if line.discount_2 >= 100:
                    discount = price_unit
                else:
                    discount = price_unit * line.discount_2 / 100
                price_unit = price_unit - discount
            if line.discount_3:
                discount = line.discount_3
                price_unit = price_unit - discount
            if line.discount_4:
                discount = line.discount_4
                price_unit = price_unit - discount

            quantity = line.product_qty
            taxes = line.taxes_id.compute_all(price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)

            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'line_sub_total': taxes['total_excluded'],
                'price_unit': price_unit
            })


    line_sub_total = fields.Monetary(compute='_get_line_subtotal',
                                     string='Line Subtotal', readonly=True, store=True, force_save=1)
    discount = fields.Float(string='Discount', digits='Discount', default=0.0)
    discount_type = fields.Selection(
        [('fixed', 'Fixed'), ('percent', 'Percent')],
        string="Discount Type",
        default="percent")
    ati_price_unit = fields.Float(string='Unit Price', required=False, digits='Product Price')

    @api.onchange('product_id')
    def onchange_ati_product_id(self):
        for rec in self:
            rec.discount_1 = 0
            rec.discount_2 = 0
            rec.discount_3 = 0
            rec.discount_4 = 0
            if rec.product_id.product_tmpl_id.hna:
                rec.ati_price_unit = rec.product_id.product_tmpl_id.hna
            elif rec.product_id.hna:
                rec.ati_price_unit = rec.product_id.hna
            else:
                rec.ati_price_unit = 0

    @api.onchange('ati_price_unit')
    def onchange_ati_price_unit(self):
        for rec in self:
            rec.price_unit = rec.ati_price_unit

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount', 'discount_type')
    def _compute_amount(self):
        return super(PurchaseOrderLine, self)._compute_amount()

    def _prepare_compute_all_values(self):
        vals = super(PurchaseOrderLine, self)._prepare_compute_all_values()
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        quantity = self.product_qty
        if self.discount_type == 'fixed':
            quantity = 1.0
            price = self.price_unit * self.product_qty - (self.discount or 0.0)
        vals.update({
            'price_unit': price,
            'quantity': quantity,
        })
        return vals

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        res.update({
            'discount_type': self.discount_type,
            'discount': self.discount,
            'discount_1': self.discount_1,
            'discount_2': self.discount_2,
            'discount_3': self.discount_3,
            'discount_4': self.discount_4,
            # 'price_unit': self.price_unit,
            'ati_price_unit': self.ati_price_unit
        })
        return res
