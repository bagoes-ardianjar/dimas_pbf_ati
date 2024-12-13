# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_promotion_po = fields.Boolean(string='Is Promotion')
    po_promotion_id = fields.Many2one('po.promotion', string='PO Promotion')

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        self.ensure_one()
        res['is_promotion_po'] = self.is_promotion_po
        return res

    def _get_stock_move_price_unit(self):
        self.ensure_one()
        if self.is_promotion_po and self.po_promotion_id and self.po_promotion_id.reward_type == 'product':
            order = self.order_id
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            purchase_line_ids = self.env['purchase.order.line'].sudo().search([
                ('order_id', '=', self.order_id.id),
                ('product_id', '=', self.product_id.id),
                ('is_promotion_po', '=', False)
            ])
            purchase_line_id = purchase_line_ids[0] if len(purchase_line_ids) > 1 else purchase_line_ids
            price_unit = purchase_line_id.line_sub_total / purchase_line_id.product_qty if  purchase_line_id.product_qty != 0 else 0
            if self.taxes_id:
                qty = self.product_qty or 1
                price_unit = self.taxes_id.with_context(round=False).compute_all(
                    price_unit, currency=self.order_id.currency_id, quantity=qty, product=self.product_id, partner=self.order_id.partner_id
                )['total_void']
                price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
            if self.product_uom.id != self.product_id.uom_id.id:
                price_unit *= self.product_uom.factor / self.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                price_unit = order.currency_id._convert(
                    price_unit, order.company_id.currency_id, self.company_id, self.date_order or fields.Date.today(), round=False)
            return price_unit
        return super(PurchaseOrderLine, self)._get_stock_move_price_unit()

class StockMove(models.Model):
    _inherit = 'stock.move'

    is_promotion_po = fields.Boolean(string='Is Promotion')

    def _get_price_unit(self):
        self.ensure_one()
        if self.is_promotion_po and self.purchase_line_id.po_promotion_id and self.purchase_line_id.po_promotion_id.reward_type == 'product'\
            and self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            purchase_line_ids = self.env['purchase.order.line'].sudo().search([
                ('order_id', '=', self.purchase_line_id.order_id.id),
                ('product_id', '=', self.purchase_line_id.product_id.id),
                ('is_promotion_po', '=', False)
            ])
            purchase_line_id = purchase_line_ids[0] if len(purchase_line_ids) > 1 else purchase_line_ids
            price_unit = purchase_line_id.line_sub_total / purchase_line_id.product_qty if  purchase_line_id.product_qty != 0 else 0
            line = self.purchase_line_id
            order = line.order_id
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            if line.taxes_id:
                qty = line.product_qty or 1
                price_unit = line.taxes_id.with_context(round=False).compute_all(
                    price_unit, currency=line.order_id.currency_id, quantity=qty, product=line.product_id, partner=line.order_id.partner_id
                )['total_void']
                price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                price_unit = order.currency_id._convert(
                    price_unit, order.company_id.currency_id, line.company_id, line.date_order or fields.Date.today(), round=False)
            return price_unit
        return super(StockMove, self)._get_price_unit()


class action_promotion_po(models.Model):
    _inherit = 'purchase.order'

    def action_promotion(self):
        for line in self.order_line:
            line.is_promo = True
        product = []
        promotion = self.env['po.promotion'].search([('status', '=', True)])

        for promotion_product in promotion:
            if promotion_product.reward_type == 'product':

                for order_line in self.order_line:
                    if (promotion_product.rule_partners_domain and promotion_product.product_ids):
                        if promotion_product.rule_date_from and promotion_product.rule_date_to:
                                for product_ids_list in promotion_product.product_ids:
                                    # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                    free_product = product_ids_list.id
                                    for customer_id in promotion_product.rule_partners_domain:
                                        customer = customer_id.id

                                        if order_line.product_id.id == free_product and customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                                date_order = datetime.strptime(str(order_line.date_order),
                                                                               "%Y-%m-%d %H:%M:%S")
                                                start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                               "%Y-%m-%d %H:%M:%S")
                                                end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                             "%Y-%m-%d %H:%M:%S")

                                                if date_order <= end_date and date_order >= start_date:
                                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':

                                                        taxes = 0
                                                        for tax_id in order_line.taxes_id:
                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                taxes = tax_id.amount
                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                tax_pph = tax_id.amount
                                                        # if order_line.taxes_id:
                                                        #     taxes = int(order_line.taxes_id.amount)
                                                        result = order_line.line_sub_total * int(taxes) / 100
                                                        total = result + order_line.line_sub_total
                                                        if total >= promotion_product.rule_minimum_amount:
                                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                                promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                                minim_qty = 1
                                                                if promotion_product.rule_min_quantity > 0:
                                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                                elif promotion_product.rule_minimum_amount > 0:
                                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                                if order_line.is_promotion == False:
                                                                    product.append((0, 0, {
                                                                        'is_promotion': True,
                                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                                        'product_id': promotion_product.reward_product_id.id,
                                                                        'po_promotion_id': promotion_product.id,
                                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                        'product_qty': reward_qty,
                                                                        'price_unit': 0, }))
                                                                    order_line.is_promotion = True
                                                            elif promotion_product.maximum_use_number == 0:
                                                                minim_qty = 1
                                                                if promotion_product.rule_min_quantity > 0:
                                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                                elif promotion_product.rule_minimum_amount > 0:
                                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                                if order_line.is_promotion == False:
                                                                    product.append((0, 0, {
                                                                        'is_promotion': True,
                                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                                        'product_id': promotion_product.reward_product_id.id,
                                                                        'po_promotion_id': promotion_product.id,
                                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                        'product_qty': reward_qty,
                                                                        'price_unit': 0, }))
                                                                    order_line.is_promotion = True


                                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                                        total = order_line.line_sub_total
                                                        if total >= promotion_product.rule_minimum_amount:
                                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                                minim_qty = 1
                                                                if promotion_product.rule_min_quantity > 0:
                                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                                elif promotion_product.rule_minimum_amount > 0:
                                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                                if order_line.is_promotion == False:
                                                                    product.append((0, 0, {
                                                                        'is_promotion': True,
                                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                                        'product_id': promotion_product.reward_product_id.id,
                                                                        'po_promotion_id': promotion_product.id,
                                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                        'product_qty': reward_qty,
                                                                        'price_unit': 0, }))
                                                                    order_line.is_promotion = True
                                                            elif promotion_product.maximum_use_number == 0:
                                                                minim_qty = 1
                                                                if promotion_product.rule_min_quantity > 0:
                                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                                elif promotion_product.rule_minimum_amount > 0:
                                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                                if order_line.is_promotion == False:
                                                                    product.append((0, 0, {
                                                                        'is_promotion': True,
                                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                                        'product_id': promotion_product.reward_product_id.id,
                                                                        'po_promotion_id': promotion_product.id,
                                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                        'product_qty': reward_qty,
                                                                        'price_unit': 0, }))
                                                                    order_line.is_promotion = True
                        else:
                                for product_ids_list in promotion_product.product_ids:
                                    # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                    free_product = product_ids_list.id
                                    customer = []
                                    for customer_id in promotion_product.rule_partners_domain:
                                        customer = customer_id.id
                                        if order_line.product_id.id == free_product and customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                            if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':

                                                taxes = 0
                                                # if order_line.taxes_id:
                                                for tax_id in order_line.taxes_id:
                                                    if tax_id.tax_group_id.name == 'PPN':
                                                        taxes = tax_id.amount
                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                        tax_pph = tax_id.amount
                                                    # taxes = int(order_line.taxes_id.amount)
                                                result = order_line.line_sub_total * int(taxes) / 100
                                                total = result + order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount :
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                'po_promotion_id': promotion_product.id,
                                                                # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                'product_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True
                                                    elif promotion_product.maximum_use_number == 0:
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                'po_promotion_id': promotion_product.id,
                                                                # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                'product_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True

                                            elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                                total = order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                'po_promotion_id': promotion_product.id,
                                                                # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                'product_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True
                                                    elif promotion_product.maximum_use_number == 0:
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                'po_promotion_id': promotion_product.id,
                                                                # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                'product_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True

                    elif promotion_product.rule_partners_domain:

                        if promotion_product.rule_date_from and promotion_product.rule_date_to:
                                # for product_ids_list in promotion_product.product_ids:
                                #     # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                #     free_product = product_ids_list.id
                                for customer_id in promotion_product.rule_partners_domain:
                                    customer = customer_id.id

                                    if customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                            date_order = datetime.strptime(str(order_line.date_order),
                                                                           "%Y-%m-%d %H:%M:%S")
                                            start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                           "%Y-%m-%d %H:%M:%S")
                                            end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                         "%Y-%m-%d %H:%M:%S")

                                            if date_order <= end_date and date_order >= start_date:
                                                if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                                    taxes = 0
                                                    # if order_line.taxes_id:
                                                    for tax_id in order_line.taxes_id:
                                                        if tax_id.tax_group_id.name == 'PPN':
                                                            taxes = tax_id.amount
                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                            tax_pph = tax_id.amount
                                                        # taxes = int(order_line.taxes_id.amount)
                                                    result = order_line.line_sub_total * int(taxes) / 100
                                                    total = result + order_line.line_sub_total
                                                    if total >= promotion_product.rule_minimum_amount:
                                                        if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                            promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                            minim_qty = 1
                                                            if promotion_product.rule_min_quantity > 0:
                                                                minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                            elif promotion_product.rule_minimum_amount > 0:
                                                                minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                            reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                            if order_line.is_promotion == False:
                                                                product.append((0, 0, {
                                                                    'is_promotion': True,
                                                                    # 'product_id': promotion_product.discount_line_product_id.id,
                                                                    'product_id': promotion_product.reward_product_id.id,
                                                                    'po_promotion_id': promotion_product.id,
                                                                    # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                    'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                    'product_qty': reward_qty,
                                                                    'price_unit': 0, }))
                                                                order_line.is_promotion = True
                                                        elif promotion_product.maximum_use_number == 0:
                                                            minim_qty = 1
                                                            if promotion_product.rule_min_quantity > 0:
                                                                minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                            elif promotion_product.rule_minimum_amount > 0:
                                                                minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                            reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                            if order_line.is_promotion == False:
                                                                product.append((0, 0, {
                                                                    'is_promotion': True,
                                                                    # 'product_id': promotion_product.discount_line_product_id.id,
                                                                    'product_id': promotion_product.reward_product_id.id,
                                                                    'po_promotion_id': promotion_product.id,
                                                                    # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                    'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                    'product_qty': reward_qty,
                                                                    'price_unit': 0, }))
                                                                order_line.is_promotion = True

                                                elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                                    total = order_line.line_sub_total
                                                    if total >= promotion_product.rule_minimum_amount:
                                                        if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                            promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                            minim_qty = 1
                                                            if promotion_product.rule_min_quantity > 0:
                                                                minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                            elif promotion_product.rule_minimum_amount > 0:
                                                                minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                            reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                            if order_line.is_promotion == False:
                                                                product.append((0, 0, {
                                                                    'is_promotion': True,
                                                                    # 'product_id': promotion_product.discount_line_product_id.id,
                                                                    'product_id': promotion_product.reward_product_id.id,
                                                                    'po_promotion_id': promotion_product.id,
                                                                    # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                    'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                    'product_qty': reward_qty,
                                                                    'price_unit': 0, }))
                                                                order_line.is_promotion = True
                                                        elif promotion_product.maximum_use_number == 0:
                                                            minim_qty = 1
                                                            if promotion_product.rule_min_quantity > 0:
                                                                minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                            elif promotion_product.rule_minimum_amount > 0:
                                                                minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                            reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                            if order_line.is_promotion == False:
                                                                product.append((0, 0, {
                                                                    'is_promotion': True,
                                                                    # 'product_id': promotion_product.discount_line_product_id.id,
                                                                    'product_id': promotion_product.reward_product_id.id,
                                                                    'po_promotion_id': promotion_product.id,
                                                                    # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                    'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                    'product_qty': reward_qty,
                                                                    'price_unit': 0, }))
                                                                order_line.is_promotion = True
                        else:

                            for customer_id in promotion_product.rule_partners_domain:
                                customer = customer_id.id
                                if customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':

                                        taxes = 0
                                        # if order_line.taxes_id:
                                        for tax_id in order_line.taxes_id:
                                            if tax_id.tax_group_id.name == 'PPN':
                                                taxes = tax_id.amount
                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                tax_pph = tax_id.amount
                                            # taxes = int(order_line.taxes_id.amount)
                                        result = order_line.line_sub_total * int(taxes) / 100
                                        total = result + order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount :
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        'po_promotion_id': promotion_product.id,
                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                        'product_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True
                                            elif promotion_product.maximum_use_number == 0:
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        'po_promotion_id': promotion_product.id,
                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                        'product_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True

                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                        total = order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        'po_promotion_id': promotion_product.id,
                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                        'product_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True
                                            elif promotion_product.maximum_use_number == 0:
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        'po_promotion_id': promotion_product.id,
                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                        'product_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True

                    elif promotion_product.product_ids:
                        if promotion_product.rule_date_from and promotion_product.rule_date_to:
                                for product_ids_list in promotion_product.product_ids:
                                    # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                    free_product = product_ids_list.id

                                    if order_line.product_id.id == free_product and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                        date_order = datetime.strptime(str(order_line.date_order),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                     "%Y-%m-%d %H:%M:%S")

                                        if date_order <= end_date and date_order >= start_date:
                                            if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':

                                                taxes = 0
                                                # if order_line.taxes_id:
                                                for tax_id in order_line.taxes_id:
                                                    if tax_id.tax_group_id.name == 'PPN':
                                                        taxes = tax_id.amount
                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                        tax_pph = tax_id.amount
                                                    # taxes = int(order_line.taxes_id.amount)
                                                result = order_line.line_sub_total * int(taxes) / 100
                                                total = result + order_line.line_sub_total

                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                'po_promotion_id': promotion_product.id,
                                                                # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                'description_product': promotion_product.reward_product_desc or '' + ' - ' + promotion_product.reward_product_id.name or '',
                                                                'product_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True
                                                    elif promotion_product.maximum_use_number == 0:
                                                        # print("TOTAL", total)
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                'po_promotion_id': promotion_product.id,
                                                                # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                'description_product': promotion_product.reward_product_desc or '' + ' - ' + promotion_product.reward_product_id.name or '',
                                                                'product_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True

                                            elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                                total = order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                'po_promotion_id': promotion_product.id,
                                                                # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                'product_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True
                                                    elif promotion_product.maximum_use_number == 0:
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                'po_promotion_id': promotion_product.id,
                                                                # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                                'product_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True
                        else:
                            for product_ids_list in promotion_product.product_ids:
                                # print("TANPA TANGGAL")
                                # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                free_product = product_ids_list.id
                                customer = []

                                if order_line.product_id.id == free_product and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':

                                        taxes = 0
                                        # if order_line.taxes_id:
                                        for tax_id in order_line.taxes_id:
                                            if tax_id.tax_group_id.name == 'PPN':
                                                taxes = tax_id.amount
                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                tax_pph = tax_id.amount
                                            # taxes = int(order_line.taxes_id.amount)
                                        result = order_line.line_sub_total * int(taxes) / 100
                                        total = result + order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount :
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        'po_promotion_id': promotion_product.id,
                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                        'product_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True
                                            elif promotion_product.maximum_use_number == 0:
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        'po_promotion_id': promotion_product.id,
                                                        # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                        'product_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True

                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            'po_promotion_id': promotion_product.id,
                                                            # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                            'product_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
                                                elif promotion_product.maximum_use_number == 0:
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            'po_promotion_id': promotion_product.id,
                                                            # 'description_product': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            'description_product': promotion_product.reward_product_desc or '' + ' - '+ promotion_product.reward_product_id.name or '',
                                                            'product_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True

            if promotion_product.reward_type == 'discount':
                if promotion_product.rule_partners_domain and promotion_product.product_ids:
                    product_ids_update = []
                    for ids in promotion_product.product_ids:
                        product_ids_update.append(ids.id)
                    if promotion_product.rule_date_from and promotion_product.rule_date_to:

                        for product_ids_list in promotion_product.product_ids:
                            # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                            free_product = product_ids_list.id
                            for customer_id in promotion_product.rule_partners_domain:
                                customer = customer_id.id
                                for order_line in self.order_line:
                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):

                                        date_order = datetime.strptime(str(order_line.date_order),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                     "%Y-%m-%d %H:%M:%S")
                                        if date_order <= end_date and date_order >= start_date:
                                            if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':

                                                taxes = 0
                                                # if order_line.taxes_id:
                                                for tax_id in order_line.taxes_id:
                                                    if tax_id.tax_group_id.name == 'PPN':
                                                        taxes = tax_id.amount
                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                        tax_pph = tax_id.amount
                                                    # taxes = int(order_line.taxes_id.amount)
                                                result = order_line.line_sub_total * int(taxes) / 100
                                                total = result + order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':

                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                    if disc_product_id:
                                                                        if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                    order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                            elif int(
                                                                                    promotion_product.discount_max_amount) == 0:

                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                                # min_price = min(
                                                                #     self.order_line.mapped('price_unit'))
                                                                min_price = min(
                                                                    product_list_update.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                                    else:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                    if disc_product_id:
                                                                        if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                    order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                            elif int(
                                                                                    promotion_product.discount_max_amount) == 0:

                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])

                                                                min_price = min(
                                                                    product_list_update.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit
                                                                        for i in product_min_price:
                                                                            i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                            elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':

                                                total = order_line.line_sub_total
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                    if disc_product_id:
                                                                        if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                    order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                            elif int(
                                                                                    promotion_product.discount_max_amount) == 0:

                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif promotion_product.discount_apply_on == 'cheapest_product':

                                                                product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])

                                                                min_price = min(
                                                                    product_list_update.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                                    else:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                subtotal = order_line.line_sub_total * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.line_sub_total + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                    if disc_product_id:
                                                                        if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                    order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                            elif int(
                                                                                    promotion_product.discount_max_amount) == 0:

                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                                # min_price = min(
                                                                #     self.order_line.mapped('price_unit'))
                                                                min_price = min(
                                                                    product_list_update.mapped('price_unit'))
                                                                po_line = self.env['purchase.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage
                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'purchase.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage

                                                                        taxes = 0
                                                                        # if order_line.taxes_id:
                                                                        for tax_id in order_line.taxes_id:
                                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                                taxes = tax_id.amount
                                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                                tax_pph = tax_id.amount
                                                                            # taxes = int(order_line.taxes_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                    else:
                        for product_ids_list in promotion_product.product_ids:
                            for customer_id in promotion_product.rule_partners_domain:
                                for order_line in self.order_line:
                                    if order_line.product_id.id == product_ids_list.id and customer_id.id == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':

                                            taxes = 0
                                            # if order_line.taxes_id:
                                            for tax_id in order_line.taxes_id:
                                                if tax_id.tax_group_id.name == 'PPN':
                                                    taxes = tax_id.amount
                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                    tax_pph = tax_id.amount
                                                # taxes = int(order_line.taxes_id.amount)
                                            result = order_line.line_sub_total * int(taxes) / 100
                                            total = result + order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()

                                                            taxes = 0
                                                            # if order_line.taxes_id:
                                                            for tax_id in order_line.taxes_id:
                                                                if tax_id.tax_group_id.name == 'PPN':
                                                                    taxes = tax_id.amount
                                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                                    tax_pph = tax_id.amount
                                                                # taxes = int(order_line.taxes_id.amount)
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal
                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])

                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()

                                                            taxes = 0
                                                            # if order_line.taxes_id:
                                                            for tax_id in order_line.taxes_id:
                                                                if tax_id.tax_group_id.name == 'PPN':
                                                                    taxes = tax_id.amount
                                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                                    tax_pph = tax_id.amount
                                                                # taxes = int(order_line.taxes_id.amount)
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])

                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    taxes = 0
                                                                    if order_line.taxes_id:
                                                                        taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()

                                                            taxes = 0
                                                            # if order_line.taxes_id:
                                                            for tax_id in order_line.taxes_id:
                                                                if tax_id.tax_group_id.name == 'PPN':
                                                                    taxes = tax_id.amount
                                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                                    tax_pph = tax_id.amount
                                                                # taxes = int(order_line.taxes_id.amount)
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])

                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()

                                                            taxes = 0
                                                            # if order_line.taxes_id:
                                                            for tax_id in order_line.taxes_id:
                                                                if tax_id.tax_group_id.name == 'PPN':
                                                                    taxes = tax_id.amount
                                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                                    tax_pph = tax_id.amount
                                                                # taxes = int(order_line.taxes_id.amount)
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])

                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif promotion_product.discount_apply_on == 'on_order':
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage
                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})
                elif promotion_product.rule_partners_domain:
                    if promotion_product.rule_date_from and promotion_product.rule_date_to:
                        for customer_id in promotion_product.rule_partners_domain:
                            for order_line in self.order_line:
                                if customer_id.id == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                    date_order = datetime.strptime(str(order_line.date_order),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                 "%Y-%m-%d %H:%M:%S")
                                    if date_order <= end_date and date_order >= start_date:
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            taxes = 0
                                            # if order_line.taxes_id:
                                            for tax_id in order_line.taxes_id:
                                                if tax_id.tax_group_id.name == 'PPN':
                                                    taxes = tax_id.amount
                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                    tax_pph = tax_id.amount
                                                # taxes = int(order_line.taxes_id.amount)
                                            result = order_line.line_sub_total * int(taxes) / 100
                                            total = result + order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            min_price = min(self.order_line.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif promotion_product.discount_apply_on == 'on_order':
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage


                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage
                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                    elif promotion_product.discount_type == 'fixed_amount':
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            min_price = min(self.order_line.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage
                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif promotion_product.discount_apply_on == 'on_order':
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage
                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                    elif promotion_product.discount_type == 'fixed_amount':
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})
                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal
                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            min_price = min(
                                                                self.order_line.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit
                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif promotion_product.discount_apply_on == 'on_order':
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage
                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                    elif promotion_product.discount_type == 'fixed_amount':
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})
                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':

                                                            taxes = 0
                                                            # if order_line.taxes_id:
                                                            for tax_id in order_line.taxes_id:
                                                                if tax_id.tax_group_id.name == 'PPN':
                                                                    taxes = tax_id.amount
                                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                                    tax_pph = tax_id.amount
                                                                # taxes = int(order_line.taxes_id.amount)
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            min_price = min(self.order_line.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:
                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif promotion_product.discount_apply_on == 'on_order':
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage
                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                    elif promotion_product.discount_type == 'fixed_amount':
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})
                    else:
                        for customer_id in promotion_product.rule_partners_domain:
                            for order_line in self.order_line:
                                if customer_id.id == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):
                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                        taxes = 0
                                        # if order_line.taxes_id:
                                        for tax_id in order_line.taxes_id:
                                            if tax_id.tax_group_id.name == 'PPN':
                                                taxes = tax_id.amount
                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                tax_pph = tax_id.amount
                                            # taxes = int(order_line.taxes_id.amount)
                                        result = order_line.line_sub_total * int(taxes) / 100
                                        total = result + order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        subtotal = order_line.line_sub_total * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.line_sub_total + subtotal
                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage


                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage


                                                            for i in order_line:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()
                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})


                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        subtotal = order_line.line_sub_total * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.line_sub_total + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})



                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100


                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            chepest_result = -diskon_percentage
                                                            for i in product_min_price:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                    elif promotion_product.discount_apply_on == 'on_order':
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage


                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage


                                                            for i in order_line:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()
                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})


                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                        total = order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':


                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:

                                                            for i in product_min_price:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage

                                                            for i in order_line:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()
                                                    order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:

                                                            for i in product_min_price:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage

                                                            for i in order_line:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()
                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                elif promotion_product.product_ids:
                    product_ids_update = []
                    for ids in promotion_product.product_ids:
                        product_ids_update.append(ids.id)
                    if promotion_product.rule_date_from and promotion_product.rule_date_to:
                        for product_ids_list in promotion_product.product_ids:
                            for order_line in self.order_line:
                                if product_ids_list.id == order_line.product_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):

                                    date_order = datetime.strptime(str(order_line.date_order),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                 "%Y-%m-%d %H:%M:%S")
                                    if date_order <= end_date and date_order >= start_date:
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':

                                            taxes = 0
                                            # if order_line.taxes_id:
                                            for tax_id in order_line.taxes_id:
                                                if tax_id.tax_group_id.name == 'PPN':
                                                    taxes = tax_id.amount
                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                    tax_pph = tax_id.amount
                                                # taxes = int(order_line.taxes_id.amount)
                                            result = order_line.line_sub_total * int(taxes) / 100
                                            total = result + order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':


                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:
                                                                            # print("DISKON amount 0")

                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit
                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage


                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':

                                            total = order_line.line_sub_total
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:
                                                                            # print("max amount kosong")

                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':

                                                            product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage


                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})


                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':

                                                            taxes = 0
                                                            # if order_line.taxes_id:
                                                            for tax_id in order_line.taxes_id:
                                                                if tax_id.tax_group_id.name == 'PPN':
                                                                    taxes = tax_id.amount
                                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                                    tax_pph = tax_id.amount
                                                                # taxes = int(order_line.taxes_id.amount)
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            subtotal = order_line.line_sub_total * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.line_sub_total + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])

                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['purchase.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    taxes = 0
                                                                    # if order_line.taxes_id:
                                                                    for tax_id in order_line.taxes_id:
                                                                        if tax_id.tax_group_id.name == 'PPN':
                                                                            taxes = tax_id.amount
                                                                        if tax_id.tax_group_id.name == 'PPH 22':
                                                                            tax_pph = tax_id.amount
                                                                        # taxes = int(order_line.taxes_id.amount)

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                taxes = 0
                                                                # if order_line.taxes_id:
                                                                for tax_id in order_line.taxes_id:
                                                                    if tax_id.tax_group_id.name == 'PPN':
                                                                        taxes = tax_id.amount
                                                                    if tax_id.tax_group_id.name == 'PPH 22':
                                                                        tax_pph = tax_id.amount
                                                                    # taxes = int(order_line.taxes_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'purchase.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                    else:
                        for product_ids_list in promotion_product.product_ids:
                            for order_line in self.order_line:
                                if product_ids_list.id == order_line.product_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.line_sub_total  >= promotion_product.rule_minimum_amount )):

                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                        taxes = 0
                                        # if order_line.taxes_id:
                                        for tax_id in order_line.taxes_id:
                                            if tax_id.tax_group_id.name == 'PPN':
                                                taxes = tax_id.amount
                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                tax_pph = tax_id.amount
                                            # taxes = int(order_line.taxes_id.amount)
                                        result = order_line.line_sub_total * int(taxes) / 100
                                        total = result + order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        subtotal = order_line.line_sub_total * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.line_sub_total + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})



                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                        # min_price = min(
                                                        #     self.order_line.mapped('price_unit'))
                                                        min_price = min(
                                                            product_list_update.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + order_line.price_unit

                                                            for i in order_line:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()
                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        subtotal = order_line.line_sub_total * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.line_sub_total + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                        # min_price = min(
                                                        #     self.order_line.mapped('price_unit'))
                                                        min_price = min(
                                                            product_list_update.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100

                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            print("O on order")
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + order_line.price_unit

                                                            for i in order_line:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()

                                                    order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})


                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                        print("discount")
                                        total = order_line.line_sub_total
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        subtotal = order_line.line_sub_total * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.line_sub_total + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})



                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                        # min_price = min(
                                                        #     self.order_line.mapped('price_unit'))
                                                        min_price = min(
                                                            product_list_update.mapped('price_unit'))
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})


                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage



                                                            for i in order_line:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                elif promotion_product.discount_type == 'fixed_amount':
                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['purchase.order.line'].sudo()

                                                        taxes = 0
                                                        # if order_line.taxes_id:
                                                        for tax_id in order_line.taxes_id:
                                                            if tax_id.tax_group_id.name == 'PPN':
                                                                taxes = tax_id.amount
                                                            if tax_id.tax_group_id.name == 'PPH 22':
                                                                tax_pph = tax_id.amount
                                                            # taxes = int(order_line.taxes_id.amount)
                                                        subtotal = order_line.line_sub_total * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.line_sub_total + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})



                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})
                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        product_list_update = self.env['purchase.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])

                                                        min_price = min(
                                                            product_list_update.mapped('price_unit'))
                                                        po_line = self.env['purchase.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})
                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                taxes = order_line.taxes_id.name


                                                                for i in product_min_price:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            chepest_result = -diskon_percentage
                                                            for i in product_min_price:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage
                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_3': promotion_product.discount_max_amount})

                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'purchase.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage


                                                                for i in order_line:
                                                                    i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'purchase.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            on_order = -diskon_percentage
                                                            taxes = 0
                                                            # if order_line.taxes_id:
                                                            for tax_id in order_line.taxes_id:
                                                                if tax_id.tax_group_id.name == 'PPN':
                                                                    taxes = tax_id.amount
                                                                if tax_id.tax_group_id.name == 'PPH 22':
                                                                    tax_pph = tax_id.amount
                                                                # taxes = int(order_line.taxes_id.amount)
                                                            subtotal = diskon_percentage * int(taxes) / 100
                                                            resultsubtotal = subtotal + order_line.price_unit

                                                            for i in order_line:
                                                                i.write({'is_discount' : True, 'discount_1': promotion_product.discount_percentage})


                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['purchase.order.line'].sudo()

                                                    for i in order_line:
                                                        i.write({'is_discount' : True, 'discount_3': promotion_product.discount_fixed_amount})

        if product:
            for p in product:
                p[2]['is_promotion_po'] = True
                # p[2]['po_promotion_id'] = promotion_product.id
        self.order_line = product

class action_promotion_po(models.Model):
    _inherit = 'purchase.order.line'

    is_promotion = fields.Boolean(string="Is Promotion", default=False)
    is_discount = fields.Boolean(string="Is Promotion", default=False)
    is_promo = fields.Boolean(string="Is Promotion", default=False)